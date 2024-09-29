# The DelugeApp class in the provided Python code is a GUI application for managing torrents using the
# Deluge torrent client API.
import time
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from requests.exceptions import SSLError
import requests
from urllib.parse import urljoin
import configparser
import os
import keyring
import sys
import subprocess
import platform
import shutil
from PIL import Image, ImageTk
from torrents_actions import show_torrent_context_menu, handle_remove_action, handle_pause_resume_action, handle_other_actions, edit_tracker
from torrents_loader import load_torrent, add_magnet
from torrents_updater import fetch_torrents, update_torrents
from ui_utils import show_message, ask_yes_no, show_about, create_menus, configure_treeview, update_button_texts, update_label_texts, update_button_state, create_entry_with_paste, configure_button_style
from ui_settings import open_settings_dialog, load_settings
from update import check_for_update
from localization import _, set_language

home_dir = os.path.expanduser("~")
config_file = os.path.join(home_dir, 'deluge_app_config.ini')

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


class DelugeApp:
    def __init__(self, master):
        self.master = master

        master.title(_("Deluge Torrent Manager"))

        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.load_config()

        style = ttk.Style("darkly")
        style.configure("Treeview", rowheight=30)
        style.configure("info.Treeview", rowheight=30)
        style.configure("Treeview.Cell", padding=(5, 5))
        style.configure("info.Treeview.Cell", padding=(5, 5))

        self.is_connected = False

        self.url_var = tk.StringVar(value=self.config.get(
            'Credentials', 'url', fallback="http://exemple_de_serveur.domaine.com"))
        self.port_var = tk.StringVar(value=self.config.get(
            'Credentials', 'port', fallback="1234"))
        self.username_var = tk.StringVar(value=self.config.get(
            'Credentials', 'username', fallback="votre_nom_utilisateur"))
        self.password_var = tk.StringVar(value=self.get_password())
        self.session = requests.Session()

        # Frame principal
        main_frame = ttk.Frame(master, padding="20 20 20 20")
        main_frame.pack(fill=BOTH, expand=YES)

        # Ajout du menu
        self.menu_bar = tk.Menu(master)
        master.config(menu=self.menu_bar)

        # Menu "Aide"
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=_("Help"), menu=help_menu)
        help_menu.add_command(
            label=_("About"), command=lambda: show_about(self.master))

        # Menu "Paramètres"
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=_("Settings"), menu=settings_menu)
        settings_menu.add_command(
            label=_("Preferences"), command=self.open_settings)
        settings_menu.add_command(
            label=_("Check for updates"), command=lambda: check_for_update(self))

        # Sous-menu "Langue"
        language_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label=_("Language"), menu=language_menu)
        language_menu.add_command(
            label=_("French"), command=lambda: self.change_app_language('fr'))
        language_menu.add_command(
            label=_("English"), command=lambda: self.change_app_language('en'))

        # Frame pour les credentials
        cred_frame = ttk.LabelFrame(main_frame, text=_(
            "Credentials"), padding="20 10 20 10")
        cred_frame.pack(fill=X, pady=10)

        # Frame pour les champs de saisie
        input_frame = ttk.Frame(cred_frame)
        # Ajoutez un peu d'espace à droite des champs
        input_frame.pack(side=LEFT, fill=Y, padx=(0, 20))

        ttk.Label(input_frame, text=_("Deluge server URL:")).grid(
            row=0, column=0, padx=5, pady=7, sticky='e')
        url_frame = create_entry_with_paste(self, input_frame, self.url_var)
        url_frame.grid(row=0, column=1, padx=5, pady=7, sticky='w')

        ttk.Label(input_frame, text=_("Port:")).grid(
            row=1, column=0, padx=5, pady=7, sticky='e')
        port_frame = create_entry_with_paste(self, input_frame, self.port_var)
        port_frame.grid(row=1, column=1, padx=5, pady=7, sticky='w')

        ttk.Label(input_frame, text=_("Username:")).grid(
            row=2, column=0, padx=5, pady=7, sticky='e')
        username_frame = create_entry_with_paste(self,
                                                 input_frame, self.username_var)
        username_frame.grid(row=2, column=1, padx=5, pady=7, sticky='w')

        ttk.Label(input_frame, text=_("Password:")).grid(
            row=3, column=0, padx=5, pady=7, sticky='e')
        password_frame = create_entry_with_paste(self,
                                                 input_frame, self.password_var, show="*")
        password_frame.grid(row=3, column=1, padx=5, pady=7, sticky='w')

        # Frame droit pour la bannière
        right_frame = ttk.Frame(cred_frame)
        right_frame.pack(side=RIGHT, fill=Y)

        self.load_banner(right_frame)

        # Configuration du style pour les boutons
        configure_button_style(self, style)

        # Frame pour les boutons de connexion
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.pack(fill=X, pady=10)

        self.connect_button = ttk.Button(self.button_frame, text=_(
            "Connection"), command=self.login, style='success.TButton')
        self.disconnect_button = ttk.Button(self.button_frame, text=_(
            "Disconnect"), command=self.disconnect, style='Purple.TButton')
        self.update_credentials_button = ttk.Button(self.button_frame, text=_(
            "Update Credentials"), command=self.update_config, style='info.TButton')
        self.clear_credentials_button = ttk.Button(self.button_frame, text=_(
            "Clear Credentials"), command=self.clear_credentials, style='danger.TButton')
        self.edit_tracker_button = ttk.Button(
            self.button_frame, text=_("Edit Tracker"),
            command=lambda: edit_tracker(self),
            style='primary.Outline.TButton')

        # Initialiser l'affichage des boutons
        update_button_state(self)

        # Ajout d'un label de statut permanent
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(fill=tk.X, pady=(0, 5))

        # Treeview pour les torrents
        self.tree = ttk.Treeview(main_frame, columns=('name', 'size', 'progress', 'down_speed',
                                 'up_speed', 'eta', 'state'), show='headings', style='info.Treeview', selectmode='extended')
        self.tree.pack(fill=BOTH, expand=YES, pady=10)

        configure_treeview(self)

        # Lier à la fois Button-2 et Button-3 pour couvrir Mac et autres systèmes
        self.tree.bind(
            "<Button-2>", lambda event: show_torrent_context_menu(self, event))
        self.tree.bind(
            "<Button-3>", lambda event: show_torrent_context_menu(self, event))
        # Ajouter également une liaison pour le clic Control sur Mac
        self.tree.bind(
            "<Control-1>", lambda event: show_torrent_context_menu(self, event))

        # Charger les paramètres
        load_settings(self.config, self.master, self.tree)

        # Frame pour les boutons de contrôle
        self.control_frame = ttk.Frame(main_frame)
        self.control_frame.pack(fill=X, pady=10)
        self.control_frame.pack_forget()  # Cacher initialement

        self.create_control_buttons()

        # Frame pour le bouton de chargement de torrent et la case à cocher
        self.load_torrent_frame = ttk.Frame(self.control_frame)
        self.load_torrent_frame.pack(side=LEFT, padx=2)

        self.load_torrent_button = ttk.Button(self.load_torrent_frame, text=_(
            "Load Torrent(s)"), command=lambda: load_torrent(self), style='primary.TButton')
        self.load_torrent_button.pack(side=LEFT)

        ttk.Label(self.load_torrent_frame, text="", width=2).pack(side=LEFT)

        self.delete_torrent_var = tk.BooleanVar()
        self.delete_torrent_checkbox = ttk.Checkbutton(self.load_torrent_frame, text=_(
            "Delete .torrent after loading"), variable=self.delete_torrent_var)
        self.delete_torrent_checkbox.pack(side=LEFT)

        self.load_torrent_frame.pack_forget()  # Cacher initialement

        self.add_magnet_button = ttk.Button(self.control_frame, text=_(
            "Send Magnet"), command=lambda: add_magnet(self), style='primary.Outline.TButton')
        self.add_magnet_button.pack(side=LEFT, padx=2)
        self.add_magnet_button.pack_forget()

        self.update_thread = None
        self.update_job = None

        self.cleanup_temp_directories()

    def load_banner(self, frame):
        try:
            banner_path = resource_path('banner.png')
            banner_image = Image.open(banner_path)
            banner_image = banner_image.resize((400, 170), Image.LANCZOS)
            banner_photo = ImageTk.PhotoImage(banner_image)

            # Création du label pour l'image et centrage
            banner_label = ttk.Label(frame, image=banner_photo)
            banner_label.image = banner_photo  # Garder une référence
            banner_label.pack(expand=True, anchor='center')
        except Exception as e:
            print(f"Error loading banner: {e}")
            # Créez un label de texte à la place si l'image ne peut pas être chargée
            banner_label = ttk.Label(frame, text="Deluge Torrent Manager")
            banner_label.pack(expand=True, anchor='center')

    def open_settings(self):
        if open_settings_dialog(self.master, self.config, self.config_file):
            load_settings(self.config, self.master, self.tree)
            if self.is_connected:
                fetch_torrents(self)
            else:
                new_color = self.config.get(
                    'Settings', 'download_color', fallback='#D3D3D3')
                self.tree.tag_configure('downloading', background=new_color)

    def create_control_buttons(self):
        buttons = [
            (_("Pause"), lambda: self.torrent_action("pause"), 'warning.TButton'),
            (_("Resume"), lambda: self.torrent_action("resume"), 'success.TButton'),
            (_("Remove"), lambda: self.torrent_action("remove"), 'danger.TButton'),
            (_("Remove with data"), lambda: self.torrent_action(
                "remove_with_data"), 'danger.Outline.TButton'),
            (_("Refresh"), lambda: fetch_torrents(self), 'info.TButton')
        ]

        for text, command, style in buttons:
            ttk.Button(self.control_frame, text=text, command=command,
                       style=style).pack(side=LEFT, padx=2)

    def load_config(self):
        if os.path.exists(config_file):
            self.config.read(config_file)
        else:
            self.config['Credentials'] = {
                'url': '', 'port': '', 'username': ''}

        if 'Settings' not in self.config:
            self.config['Settings'] = {}

        if 'download_color' not in self.config['Settings']:
            self.config['Settings']['download_color'] = '#D3D3D3'
        if 'window_size' not in self.config['Settings']:
            self.config['Settings']['window_size'] = '1200x900'

        if not os.path.exists(config_file):
            with open(config_file, 'w') as configfile:
                self.config.write(configfile)

    def get_password(self):
        username = self.config.get('Credentials', 'username', fallback="")
        if username:
            return keyring.get_password("DelugeApp", username) or ""
        return ""

    def disconnect(self):
        self.is_connected = False
        if self.update_job:
            self.master.after_cancel(self.update_job)
            self.update_job = None
        self.session = None
        self.tree.delete(*self.tree.get_children())
        self.load_torrent_frame.pack_forget()
        self.add_magnet_button.pack_forget()
        self.control_frame.pack_forget()
        self.disconnect_button.pack_forget()
        self.connect_button.pack(side=LEFT, padx=5)
        self.status_label.config(text="")
        update_button_state(self)

    def update_config(self):
        new_config = {
            'url': self.url_var.get().strip(),
            'port': self.port_var.get().strip(),
            'username': self.username_var.get().strip()
        }
        new_password = self.password_var.get().strip()

        missing_credentials = [key for key,
                               value in new_config.items() if not value]
        if not new_password:
            missing_credentials.append('password')

        if missing_credentials:
            missing_fields = ', '.join(missing_credentials)
            show_message(self.master, _("Error"), _(
                "The following fields are missing: {}").format(missing_fields))
            return

        old_config = dict(self.config['Credentials'])
        old_password = self.get_password()

        config_changed = new_config != old_config
        password_changed = new_password != old_password

        if config_changed or password_changed:
            self.config['Credentials'] = new_config
            with open(config_file, 'w') as configfile:
                self.config.write(configfile)

            if new_config['username'] and password_changed:
                keyring.set_password(
                    "DelugeApp", new_config['username'], new_password)
            self.disconnect()
            show_message(self.master, _("Update"), _(
                "Credentials have been updated."))
        else:
            show_message(self.master, _("Information"),
                         _("No changes in credentials."))

    def login(self):
        url = self.url_var.get()
        port = self.port_var.get()
        username = self.username_var.get()
        password = self.password_var.get()

        if not url or not port or not username or not password:
            show_message(self.master, _("Error"), _(
                "Please fill in all required fields."))
            return

        self.base_url = f"{url}:{port}/"
        self.login_url = urljoin(self.base_url, "json")

        self.session = requests.Session()

        try:
            response = self.session.post(
                self.login_url, data={"password": password})
            if response.status_code != 200:
                show_message(self.master, _("Error"), _(
                    "Initial authentication failed. Code: {}").format(response.status_code))
                self.disconnect()
                return

            response = self.session.post(self.login_url, json={
                "method": "auth.login",
                "params": [password],
                "id": 1
            })
            data = response.json()

            if data.get('result'):
                response = self.session.post(self.login_url, json={
                    "method": "auth.check_session",
                    "params": [],
                    "id": 2
                })
                session_data = response.json()

                if session_data.get('result'):
                    show_message(self.master, _("Success"),
                                 _("Connection successful!"))
                    self.is_connected = True
                    update_button_state(self)
                    self.update_job = self.master.after(
                        5000, lambda: update_torrents(self))

                    if 'Credentials' not in self.config:
                        self.config['Credentials'] = {}

                    old_config = dict(self.config['Credentials'])
                    old_password = self.get_password()
                    new_config = {
                        'url': url,
                        'port': port,
                        'username': username
                    }

                    if new_config != old_config or password != old_password:
                        self.config['Credentials'] = new_config
                        with open(self.config_file, 'w') as configfile:
                            self.config.write(configfile)
                        if username:
                            keyring.set_password(
                                "DelugeApp", username, password)
                            show_message(self.master, _("Update"), _(
                                "New credentials have been saved."))

                    self.connect_button.pack_forget()
                    self.load_torrent_frame.pack(side=LEFT, padx=2)
                    self.add_magnet_button.pack(side=LEFT, padx=2)
                    self.control_frame.pack(side=LEFT, padx=2)
                    self.disconnect_button.pack(side=LEFT, padx=5)
                    fetch_torrents(self)
                else:
                    show_message(self.master, _("Error"), _(
                        "Unable to verify session. Please try again."))
                    self.disconnect()
            else:
                show_message(self.master, _("Error"), _(
                    "JSON-RPC API authentication failed. Response: {}").format(data))
                self.disconnect()
        except SSLError as e:
            show_message(self.master, _("SSL Error"), _(
                "SSL certificate error: {}").format(str(e)))
            self.disconnect()
            return
        except requests.RequestException as e:
            show_message(self.master, _("Error"), _(
                "Connection error: {}").format(str(e)))
            self.disconnect()

    def clear_credentials(self):
        if not any(self.config['Credentials'].values()) and not self.get_password():
            show_message(self.master, _("Information"),
                         _("No credentials to clear."))
            return

        confirm = ask_yes_no(self.master, _("Confirmation"), _(
            "Are you sure you want to clear all credentials?"))
        if confirm:
            self.config['Credentials'] = {
                'url': '', 'port': '', 'username': ''}
            with open(config_file, 'w') as configfile:
                self.config.write(configfile)

            old_username = self.username_var.get()
            if old_username:
                keyring.delete_password("DelugeApp", old_username)

            self.url_var.set('')
            self.port_var.set('')
            self.username_var.set('')
            self.password_var.set('')
            self.disconnect()
            show_message(self.master, _("Success"), _(
                "All credentials have been cleared."))

    def torrent_action(self, action):
        if not self.is_connected:
            show_message(self.master, _("Error"), _("You are not connected."))
            return

        selected_items = self.tree.selection()
        if not selected_items:
            show_message(self.master, _("Warning"), _(
                "Please select at least one torrent."), "warning")
            return

        torrents = [
            {
                'hash': self.tree.item(item)['tags'][0],
                'name': self.tree.item(item)['values'][0],
                'state': self.tree.item(item)['values'][6]
            }
            for item in selected_items
        ]

        if action in ["remove", "remove_with_data"]:
            handle_remove_action(self, action, torrents)
        elif action in ["pause", "resume"]:
            handle_pause_resume_action(self, action, torrents)
        else:
            handle_other_actions(self, action, torrents)

    def on_closing(self):
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
        self.master.destroy()

    def cleanup_temp_directories(self):
        if getattr(sys, 'frozen', False):
            try:
                # Obtenir le chemin du répertoire temporaire actuel
                current_temp_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
                parent_dir = os.path.dirname(current_temp_dir)

                print(f"Current temp directory: {current_temp_dir}")
                print(f"Parent directory: {parent_dir}")

                for item in os.listdir(parent_dir):
                    item_path = os.path.join(parent_dir, item)
                    if item.startswith("_MEI") and os.path.isdir(item_path) and item_path != current_temp_dir:
                        try:
                            shutil.rmtree(item_path, ignore_errors=True)
                            print(f"Cleaned up directory: {item_path}")
                        except Exception as e:
                            print(f"Error cleaning up {item_path}: {e}")

            except Exception as e:
                print(f"Error during cleanup: {e}")

    def change_app_language(self, lang):
        try:
            key_language = self.config['Settings'].get('language', 'fr')

            if lang != key_language:
                self.config['Settings']['language'] = lang
                config_path = os.path.abspath(self.config_file)
                with open(self.config_file, 'w') as configfile:
                    self.config.write(configfile)

                message = _(
                    "Changing the language will restart the application. Do you want to continue?")

                if ask_yes_no(self.master, _("Confirm Language Change"), message):
                    self.restart_application()
            else:
                show_message(self.master, _("Information"), _(
                    "The selected language is already in use."))
        except Exception as e:
            show_message(self.master, _("Error"), _(
                "An error occurred while changing the language."))

    
    def restart_application(self):
        try:
            if getattr(sys, 'frozen', False):
                
                exe_path = sys.executable
                
                if platform.system() == 'Windows':
                    temp_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(exe_path)
                
                    parent_dir = os.path.dirname(temp_dir)
                
                    temp_copy_dir = os.path.join(parent_dir, f'_MEI_copy_{os.getpid()}')
                    
                    if os.path.commonpath([temp_dir, temp_copy_dir]) != parent_dir:
                        raise Exception("The copy operation is not happening within the same parent directory.")
                    
                    shutil.copytree(temp_dir, temp_copy_dir)
                    current_pid = os.getpid()
                    temp_file_path = os.path.join(parent_dir, f'restart{current_pid}.bat')
                    delete_file_path = os.path.join(parent_dir, f'delete{current_pid}.bat')

                    with open(temp_file_path, 'w') as temp_file:
                        temp_file.write('@echo off\n')
                        temp_file.write(f'set ORIGINAL_PID={current_pid}\n')
                        temp_file.write(f'set RESTART_PID=%RANDOM%%RANDOM%\n')
                        temp_file.write('echo %RESTART_PID% > "%TEMP%\\restart_pid.txt"\n')
                        temp_file.write(f'echo Waiting for PID %ORIGINAL_PID% to exit...\n')
                        temp_file.write(':wait_loop\n')
                        temp_file.write(f'tasklist /FI "PID eq %ORIGINAL_PID%" 2>NUL | find /I /N "%ORIGINAL_PID%">NUL\n')
                        temp_file.write('if "%ERRORLEVEL%"=="0" (\n')
                        temp_file.write('    ping 127.0.0.1 -n 2 > nul\n')
                        temp_file.write('    goto wait_loop\n')
                        temp_file.write(')\n')
                        temp_file.write(f'echo Process %ORIGINAL_PID% has exited.\n')
                        temp_file.write(f'ren "{temp_copy_dir}" "{os.path.basename(temp_dir)}"\n')
                        temp_file.write(f'cd /d "{os.path.dirname(exe_path)}"\n')
                        temp_file.write(f'start "" "{exe_path}"\n')
                        temp_file.write(':check_new_process\n')
                        temp_file.write(f'tasklist /FI "IMAGENAME eq {os.path.basename(exe_path)}" 2>NUL | find /I /N "{os.path.basename(exe_path)}">NUL\n')
                        temp_file.write('if "%ERRORLEVEL%"=="1" (\n')
                        temp_file.write('    ping 127.0.0.1 -n 2 > nul\n')
                        temp_file.write('    goto check_new_process\n')
                        temp_file.write(')\n')
                        temp_file.write(f'start "" /b cmd /c "{delete_file_path}"\n')
                        temp_file.write('exit\n')

                    with open(delete_file_path, 'w') as delete_file:
                        delete_file.write('@echo off\n')
                        delete_file.write('setlocal enabledelayedexpansion\n')
                        delete_file.write('set /p RESTART_PID=<"%TEMP%\\restart_pid.txt"\n')
                        delete_file.write('del "%TEMP%\\restart_pid.txt"\n')
                        delete_file.write(':check_restart\n')
                        delete_file.write('for /f "tokens=2" %%a in (\'tasklist /fi "PID eq %RESTART_PID%" /fo list ^| find "PID:"\') do set FOUND_PID=%%a\n')
                        delete_file.write('if "!FOUND_PID!"=="%RESTART_PID%" (\n')
                        delete_file.write('    taskkill /F /PID %RESTART_PID%\n')
                        delete_file.write('    ping 127.0.0.1 -n 2 > nul\n')
                        delete_file.write('    goto check_restart\n')
                        delete_file.write(')\n')
                        delete_file.write(f'for /d %%i in ("{parent_dir}\\_MEI_copy_*") do (\n')
                        delete_file.write('    rd /s /q "%%i"\n')
                        delete_file.write(')\n')
                        delete_file.write(f'del "{temp_file_path}"\n')
                        delete_file.write('(goto) 2>nul & del "%~f0"\n')

                    subprocess.Popen(['cmd', '/c', 'start', '/b', temp_file_path], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                    time.sleep(1)

                elif platform.system() == 'Linux':
                    temp_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(exe_path)
                    parent_dir = os.path.dirname(temp_dir)
                    temp_copy_dir = os.path.join(parent_dir, f'_MEI_copy_{os.getpid()}')
                    
                    if os.path.commonpath([temp_dir, temp_copy_dir]) != parent_dir:
                        raise Exception("The copy operation is not happening within the same parent directory.")
                    
                    shutil.copytree(temp_dir, temp_copy_dir)
                    
                    restart_script_path = os.path.join(parent_dir, f'restart_{os.getpid()}.sh')
                    with open(restart_script_path, 'w') as restart_script:
                        restart_script.write(f"""#!/bin/bash
    while ps -p {os.getpid()} > /dev/null; do sleep 1; done
    mv "{temp_copy_dir}" "{temp_dir}"
    "{exe_path}" &
    rm -f "{restart_script_path}"
    """)
                    
                    os.chmod(restart_script_path, 0o755)
                    subprocess.Popen(['/bin/bash', restart_script_path])
                else:
                    
                    subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
            else:
                python = sys.executable
                script_path = os.path.abspath(sys.argv[0])
                subprocess.Popen([python, script_path], cwd=os.path.dirname(script_path))
            
            print("Closing the current application...")
            self.master.after(100, self.master.destroy)
        except Exception as e:
            print(f"Error during application restart: {e}")
        finally:
            sys.exit()


    def update_ui_language(self):
        self.master.title(_("Deluge Torrent Manager"))
        create_menus(self)
        configure_treeview(self)
        update_button_texts(self)
        update_label_texts(self)
        if self.is_connected:
            fetch_torrents(self)


def load_language():
    config = configparser.ConfigParser()

    if os.path.exists(config_file):
        config.read(config_file)
    else:
        config['Settings'] = {'language': 'fr'}
        with open(config_file, 'w') as configfile:
            config.write(configfile)

    lang = config.get('Settings', 'language', fallback='fr')
    set_language(lang)


def main():
    load_language()
    root = tk.Tk()
    app = DelugeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
