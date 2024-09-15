# The DelugeApp class in the provided Python code is a GUI application for managing torrents using the
# Deluge torrent client API.
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
from PIL import Image, ImageTk
from torrents_actions import handle_remove_action, handle_pause_resume_action, handle_other_actions
from torrents_loader import load_torrent, add_magnet
from torrents_updater import fetch_torrents, update_torrents
from ui_utils import show_message, ask_yes_no

home_dir = os.path.expanduser("~")
config_file = os.path.join(home_dir, 'deluge_app_config.ini')


class DelugeApp:
    def __init__(self, master):
        self.master = master
        master.title("Deluge Torrent Manager")
        master.geometry("1200x900")

        style = ttk.Style("darkly")
        style.configure("Treeview", rowheight=30)
        style.configure("info.Treeview", rowheight=30)
        style.configure("Treeview.Cell", padding=(5, 5))
        style.configure("info.Treeview.Cell", padding=(5, 5))

        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.is_connected = False
        self.load_config()

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

        # Frame pour les credentials
        cred_frame = ttk.LabelFrame(
            main_frame, text="Credentials", padding="20 10 20 10")
        cred_frame.pack(fill=X, pady=10)

        # Frame gauche pour les champs de saisie
        left_frame = ttk.Frame(cred_frame)
        left_frame.pack(side=LEFT, fill=Y, expand=False)

        ttk.Label(left_frame, text="URL du serveur Deluge:").grid(
            row=0, column=0, padx=5, pady=7, sticky='e')
        ttk.Entry(left_frame, textvariable=self.url_var, width=40).grid(
            row=0, column=1, padx=5, pady=7, sticky='we')

        ttk.Label(left_frame, text="Port:").grid(
            row=1, column=0, padx=5, pady=7, sticky='e')
        ttk.Entry(left_frame, textvariable=self.port_var).grid(
            row=1, column=1, padx=5, pady=7, sticky='we')

        ttk.Label(left_frame, text="Nom d'utilisateur:").grid(
            row=2, column=0, padx=5, pady=7, sticky='e')
        ttk.Entry(left_frame, textvariable=self.username_var).grid(
            row=2, column=1, padx=5, pady=7, sticky='we')

        ttk.Label(left_frame, text="Mot de passe:").grid(
            row=3, column=0, padx=5, pady=7, sticky='e')
        ttk.Entry(left_frame, textvariable=self.password_var,
                  show="*").grid(row=3, column=1, padx=5, pady=7, sticky='we')

        # Frame droit pour la bannière
        right_frame = ttk.Frame(cred_frame)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        banner_path = None

        # Chargement et redimensionnement de l'image
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller exécutable
            banner_path = os.path.join(sys._MEIPASS, 'banner.png')
        else:
           # Environnement de développement
            banner_path = os.path.join(os.path.dirname(
                __file__), 'banner.png')

        banner_image = Image.open(banner_path)
        # Ajustez la taille selon vos besoins
        banner_image = banner_image.resize((400, 170), Image.LANCZOS)
        banner_photo = ImageTk.PhotoImage(banner_image)

        # Création du label pour l'image et centrage
        banner_label = ttk.Label(right_frame, image=banner_photo)
        banner_label.image = banner_photo  # Garder une référence
        banner_label.pack(expand=True, anchor='center')

        # Frame pour les boutons de connexion
        style.configure("Purple.TButton",
                        background="#8E44AD",  # Couleur mauve
                        foreground="white",
                        borderwidth=0,  # Supprimer la bordure
                        focuscolor="#8E44AD",  # Couleur quand le bouton a le focus
                        lightcolor="#8E44AD",
                        darkcolor="#8E44AD",
                        relief="flat",  # Pas de relief
                        padding=(10, 5))

        style.map("Purple.TButton",
                  background=[('active', '#9B59B6'),  # Mauve plus clair au survol
                              # Mauve plus foncé quand pressé
                              ('pressed', '#7D3C98')],
                  foreground=[('active', 'white'),
                              ('pressed', 'white')],
                  bordercolor=[('active', '#9B59B6'),
                               ('pressed', '#7D3C98')],
                  lightcolor=[('active', '#9B59B6'),
                              ('pressed', '#7D3C98')],
                  darkcolor=[('active', '#9B59B6'),
                             ('pressed', '#7D3C98')])

        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.pack(fill=X, pady=10)

        self.connect_button = ttk.Button(
            self.button_frame, text="Connexion", command=self.login, style='success.TButton')

        self.disconnect_button = ttk.Button(
            self.button_frame, text="Déconnecter", command=self.disconnect, style='Purple.TButton')

        self.update_credentials_button = ttk.Button(
            self.button_frame, text="Mise à jour des credentials",
            command=self.update_config, style='info.TButton')

        self.clear_credentials_button = ttk.Button(
            self.button_frame, text="Effacer les credentials",
            command=self.clear_credentials, style='danger.TButton')

        # Initialiser l'affichage des boutons
        self.update_button_state()

        # Ajout d'un label de statut permanent
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(fill=tk.X, pady=(0, 5))

        # Treeview pour les torrents
        self.tree = ttk.Treeview(main_frame, columns=('name', 'size', 'progress', 'down_speed',
                                 'up_speed', 'eta', 'state'), show='headings', style='info.Treeview', selectmode='extended')
        self.tree.pack(fill=BOTH, expand=YES, pady=10)

        self.tree.tag_configure('oddrow', background='#2a3038')
        self.tree.tag_configure('evenrow', background='#212529')
        self.tree.tag_configure('downloading', background='#D3D3D3')

        self.tree.heading('name', text='Nom')
        self.tree.heading('size', text='Taille')
        self.tree.heading('progress', text='Progression')
        self.tree.heading('down_speed', text='Vitesse DL')
        self.tree.heading('up_speed', text='Vitesse UL')
        self.tree.heading('eta', text='ETA')
        self.tree.heading('state', text='État')

        self.tree.column('name', width=300, anchor='w')
        self.tree.column('size', width=100, anchor='center')
        self.tree.column('progress', width=100, anchor='center')
        self.tree.column('down_speed', width=100, anchor='center')
        self.tree.column('up_speed', width=100, anchor='center')
        self.tree.column('eta', width=100, anchor='center')
        self.tree.column('state', width=100, anchor='center')

        # Frame pour les boutons de contrôle
        self.control_frame = ttk.Frame(main_frame)
        self.control_frame.pack(fill=X, pady=10)
        self.control_frame.pack_forget()  # Cacher initialement

        ttk.Button(self.control_frame, text="Pause", command=lambda: self.torrent_action(
            "pause"), style='warning.TButton').pack(side=LEFT, padx=2)
        ttk.Button(self.control_frame, text="Reprise", command=lambda: self.torrent_action(
            "resume"), style='success.TButton').pack(side=LEFT, padx=2)
        ttk.Button(self.control_frame, text="Enlever", command=lambda: self.torrent_action(
            "remove"), style='danger.TButton').pack(side=LEFT, padx=2)
        ttk.Button(self.control_frame, text="Supprimer avec données", command=lambda: self.torrent_action(
            "remove_with_data"), style='danger.Outline.TButton').pack(side=LEFT, padx=2)
        ttk.Button(self.control_frame, text="Refresh", command=lambda: fetch_torrents(
            self), style='info.TButton').pack(side=LEFT, padx=2)

        # Frame pour le bouton de chargement de torrent et la case à cocher
        self.load_torrent_frame = ttk.Frame(self.control_frame)
        self.load_torrent_frame.pack(side=LEFT, padx=2)

        self.load_torrent_button = ttk.Button(
            self.load_torrent_frame, text="Charger torrent(s)", command=lambda: load_torrent(self), style='primary.TButton')

        self.load_torrent_button.pack(side=LEFT)

        ttk.Label(self.load_torrent_frame, text="", width=2).pack(side=LEFT)

        self.delete_torrent_var = tk.BooleanVar()
        self.delete_torrent_checkbox = ttk.Checkbutton(
            self.load_torrent_frame, text="Supprimer .torrent après chargement", variable=self.delete_torrent_var)
        self.delete_torrent_checkbox.pack(side=LEFT)

        self.load_torrent_frame.pack_forget()  # Cacher initialement

        self.add_magnet_button = ttk.Button(
            self.control_frame, text="Coller un magnet", command=lambda: add_magnet(self), style='primary.Outline.TButton')
        self.add_magnet_button.pack(side=LEFT, padx=2)
        self.add_magnet_button.pack_forget()

        self.update_thread = None
        self.update_job = None

    def load_config(self):
        if os.path.exists(config_file):
            self.config.read(config_file)
        else:
            self.config['Credentials'] = {
                'url': '', 'port': '', 'username': ''}

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
        self.session = None  # Réinitialiser la session
        # Vider la liste des torrents
        self.tree.delete(*self.tree.get_children())
        self.load_torrent_frame.pack_forget()
        self.add_magnet_button.pack_forget()
        self.control_frame.pack_forget()
        self.disconnect_button.pack_forget()
        self.connect_button.pack(side=LEFT, padx=5)
        self.status_label.config(text="")
        self.update_button_state()

    def update_config(self):
        new_config = {
            'url': self.url_var.get().strip(),
            'port': self.port_var.get().strip(),
            'username': self.username_var.get().strip()
        }
        new_password = self.password_var.get().strip()

        # Vérification des credentials manquants
        missing_credentials = [key for key,
                               value in new_config.items() if not value]
        if not new_password:
            missing_credentials.append('password')

        if missing_credentials:
            missing_fields = ', '.join(missing_credentials)
            show_message(self.master,
                         "Erreur", f"Les champs suivants sont manquants : {missing_fields}")
            return

        old_config = dict(self.config['Credentials'])
        old_password = self.get_password()

        config_changed = new_config != old_config
        password_changed = new_password != old_password

        if config_changed or password_changed:
            self.config['Credentials'] = new_config
            with open(config_file, 'w') as configfile:
                self.config.write(configfile)

            # Mise à jour du mot de passe dans le keyring si nécessaire
            if new_config['username'] and password_changed:
                keyring.set_password(
                    "DelugeApp", new_config['username'], new_password)
            self.disconnect()
            show_message(self.master,
                         "Mise à jour", "Les credentials ont été mis à jour.")
        else:
            show_message(self.master,
                         "Information", "Aucun changement dans les credentials.")

    def update_button_state(self):
        if self.is_connected:
            self.connect_button.pack_forget()
            self.disconnect_button.pack(side=LEFT, padx=5)
            self.update_credentials_button.pack_forget()
            self.clear_credentials_button.pack_forget()
        else:
            self.disconnect_button.pack_forget()
            self.connect_button.pack(side=LEFT, padx=5)
            self.update_credentials_button.pack(side=LEFT, padx=5)
            self.clear_credentials_button.pack(side=LEFT, padx=5)

    def login(self):
        url = self.url_var.get()
        port = self.port_var.get()
        username = self.username_var.get()
        password = self.password_var.get()

        if not url or not port or not username or not password:
            show_message(self.master,
                         "Erreur", "Veuillez remplir tous les champs obligatoires.")
            return

        self.base_url = f"{url}:{port}/"
        self.login_url = urljoin(self.base_url, "json")

        self.session = requests.Session()

        try:
            # Première étape : authentification initiale
            response = self.session.post(
                self.login_url, data={"password": password})
            if response.status_code != 200:
                show_message(self.master,
                             "Erreur", f"Échec de l'authentification initiale. Code: {response.status_code}")
                self.disconnect()
                return

        # Deuxième étape : authentification à l'API JSON-RPC
            response = self.session.post(self.login_url, json={
                "method": "auth.login",
                "params": [password],
                "id": 1
            })
            data = response.json()

            if data.get('result'):
                # Troisième étape : vérification de la session
                response = self.session.post(self.login_url, json={
                    "method": "auth.check_session",
                    "params": [],
                    "id": 2
                })
                session_data = response.json()

                if session_data.get('result'):
                    show_message(self.master, "Succès", "Connexion réussie!")
                    self.is_connected = True
                    self.update_button_state()
                    # Démarrer la mise à jour périodique
                    self.update_job = self.master.after(
                        5000, lambda: update_torrents(self))

                # Mise à jour des credentials si nécessaire
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
                            show_message(self.master,
                                         "Mise à jour", "Les nouveaux credentials ont été sauvegardés.")

                    self.connect_button.pack_forget()  # Cacher le bouton Connexion
                    self.load_torrent_frame.pack(side=LEFT, padx=2)
                    self.add_magnet_button.pack(side=LEFT, padx=2)
                    # unhide control_frame
                    self.control_frame.pack(side=LEFT, padx=2)
                    # Afficher le bouton Déconnecter
                    self.disconnect_button.pack(side=LEFT, padx=5)
                    fetch_torrents(self)
                else:
                    show_message(self.master,
                                 "Erreur", "Impossible de vérifier la session. Veuillez réessayer.")
                    self.disconnect()
            else:
                show_message(self.master,
                             "Erreur", f"Échec de l'authentification à l'API JSON-RPC. Réponse: {data}")
                self.disconnect()
        except SSLError as e:
            show_message(self.master,
                         "Erreur SSL", f"Erreur de certificat SSL : {str(e)}")
            self.disconnect()
            return
        except requests.RequestException as e:
            show_message(self.master, "Erreur",
                         f"Erreur de connexion: {str(e)}")
            self.disconnect()

    def clear_credentials(self):
        if not any(self.config['Credentials'].values()) and not self.get_password():
            show_message(self.master, "Information",
                         "Aucun credential à effacer.")
            return

        confirm = ask_yes_no(self.master,
                             "Confirmation", "Êtes-vous sûr de vouloir effacer tous les credentials?")
        if confirm:
            # Effacer les données du fichier de configuration
            self.config['Credentials'] = {
                'url': '', 'port': '', 'username': ''}
            with open(config_file, 'w') as configfile:
                self.config.write(configfile)

            # Effacer le mot de passe du keyring
            old_username = self.username_var.get()
            if old_username:
                keyring.delete_password("DelugeApp", old_username)

            # Réinitialiser les variables de l'interface
            self.url_var.set('')
            self.port_var.set('')
            self.username_var.set('')
            self.password_var.set('')
            self.disconnect()
            show_message(self.master,
                         "Succès", "Tous les credentials ont été effacés.")

    def torrent_action(self, action):
        if not self.is_connected:
            show_message(self.master, "Erreur", "Vous n'êtes pas connecté.")
            return

        selected_items = self.tree.selection()
        if not selected_items:
            show_message(self.master,
                         "Avertissement", "Veuillez sélectionner au moins un torrent.", "warning")
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
        # Méthode à appeler lors de la fermeture de l'application
        if self.update_thread and self.update_thread.is_alive():
            # Attendre au maximum 1 seconde
            self.update_thread.join(timeout=1.0)
        self.master.destroy()


def main():
    root = tk.Tk()
    app = DelugeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
