# The DelugeApp class in the provided Python code is a GUI application for managing torrents using the
# Deluge torrent client API.
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from requests.exceptions import SSLError
import requests
from urllib.parse import urljoin
import base64
import configparser
import os
import keyring
import threading
import time

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

        ttk.Label(cred_frame, text="URL du serveur Deluge:").grid(
            row=0, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(cred_frame, textvariable=self.url_var, width=40).grid(
            row=0, column=1, padx=5, pady=5, sticky='we')

        ttk.Label(cred_frame, text="Port:").grid(
            row=1, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(cred_frame, textvariable=self.port_var).grid(
            row=1, column=1, padx=5, pady=5, sticky='we')

        ttk.Label(cred_frame, text="Nom d'utilisateur:").grid(
            row=2, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(cred_frame, textvariable=self.username_var).grid(
            row=2, column=1, padx=5, pady=5, sticky='we')

        ttk.Label(cred_frame, text="Mot de passe:").grid(
            row=3, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(cred_frame, textvariable=self.password_var,
                  show="*").grid(row=3, column=1, padx=5, pady=5, sticky='we')

        # Frame pour les boutons de connexion
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)

        self.connect_button = ttk.Button(
            button_frame, text="Connexion", command=self.login, style='success.TButton')
        self.connect_button.pack(side=LEFT, padx=5)

        ttk.Button(button_frame, text="Mise à jour des credentials",
                   command=self.update_config, style='info.TButton').pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Effacer les credentials",
                   command=self.clear_credentials, style='danger.TButton').pack(side=LEFT, padx=5)

        self.disconnect_button = ttk.Button(
            button_frame, text="Déconnecter", command=self.disconnect, style='warning.TButton')
        self.disconnect_button.pack(side=LEFT, padx=5)
        self.disconnect_button.pack_forget()

        # Ajout d'un label de statut permanent
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(fill=tk.X, pady=(0, 5))

        # Treeview pour les torrents
        self.tree = ttk.Treeview(main_frame, columns=('name', 'size', 'progress', 'down_speed',
                                 'up_speed', 'eta', 'state'), show='headings', style='info.Treeview')
        self.tree.pack(fill=BOTH, expand=YES, pady=10)

        self.tree.tag_configure('oddrow', background='#2a3038')
        self.tree.tag_configure('evenrow', background='#212529')

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
        ttk.Button(self.control_frame, text="Resume", command=lambda: self.torrent_action(
            "resume"), style='success.TButton').pack(side=LEFT, padx=2)
        ttk.Button(self.control_frame, text="Remove", command=lambda: self.torrent_action(
            "remove"), style='danger.TButton').pack(side=LEFT, padx=2)
        ttk.Button(self.control_frame, text="Remove with Data", command=lambda: self.torrent_action(
            "remove_with_data"), style='danger.Outline.TButton').pack(side=LEFT, padx=2)
        ttk.Button(self.control_frame, text="Refresh", command=self.fetch_torrents,
                   style='info.TButton').pack(side=LEFT, padx=2)

        # Frame pour le bouton de chargement de torrent et la case à cocher
        self.load_torrent_frame = ttk.Frame(self.control_frame)
        self.load_torrent_frame.pack(side=LEFT, padx=2)

        self.load_torrent_button = ttk.Button(
            self.load_torrent_frame, text="Charger un torrent", command=self.load_torrent, style='primary.TButton')
        self.load_torrent_button.pack(side=LEFT)

        ttk.Label(self.load_torrent_frame, text="", width=2).pack(side=LEFT)

        self.delete_torrent_var = tk.BooleanVar()
        self.delete_torrent_checkbox = ttk.Checkbutton(
            self.load_torrent_frame, text="Supprimer .torrent après chargement", variable=self.delete_torrent_var)
        self.delete_torrent_checkbox.pack(side=LEFT)

        self.load_torrent_frame.pack_forget()  # Cacher initialement

        self.add_magnet_button = ttk.Button(
            self.control_frame, text="Coller un magnet", command=self.add_magnet, style='primary.Outline.TButton')
        self.add_magnet_button.pack(side=LEFT, padx=2)
        self.add_magnet_button.pack_forget()

        self.update_thread = None

    def show_message(self, title, message, message_type="info"):
        if message_type == "error":
            icon = "error"
        elif message_type == "warning":
            icon = "warning"
        else:
            icon = "info"

        top = tk.Toplevel(self.master)
        top.title(title)
        top.geometry("300x150")
        top.resizable(False, False)

        ttk.Label(top, text=message, wraplength=250,
                  justify="center").pack(expand=True, pady=10)
        ttk.Button(top, text="OK", command=top.destroy).pack(pady=10)

        top.transient(self.master)
        top.grab_set()
        self.master.wait_window(top)

    def ask_yes_no(self, title, message):
        result = [False]  # Pour stocker le résultat

        top = tk.Toplevel(self.master)
        top.title(title)
        top.geometry("300x150")
        top.resizable(False, False)

        ttk.Label(top, text=message, wraplength=250,
                  justify="center").pack(expand=True, pady=10)

        button_frame = ttk.Frame(top)
        button_frame.pack(pady=10)

        def on_yes():
            result[0] = True
            top.destroy()

        def on_no():
            result[0] = False
            top.destroy()

        ttk.Button(button_frame, text="Oui", command=on_yes,
                   style='success.TButton').pack(side="left", padx=10)
        ttk.Button(button_frame, text="Non", command=on_no,
                   style='danger.TButton').pack(side="left", padx=10)

        top.transient(self.master)
        top.grab_set()
        self.master.wait_window(top)

        return result[0]

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
        self.session = None  # Réinitialiser la session
        # Vider la liste des torrents
        self.tree.delete(*self.tree.get_children())
        self.load_torrent_frame.pack_forget()
        self.add_magnet_button.pack_forget()
        self.control_frame.pack_forget()
        self.disconnect_button.pack_forget()
        self.connect_button.pack(side=LEFT, padx=5)

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
            self.show_message(
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

            self.show_message(
                "Mise à jour", "Les credentials ont été mis à jour.")
            self.disconnect()
        else:
            self.show_message(
                "Information", "Aucun changement dans les credentials.")

    def login(self):
        url = self.url_var.get()
        port = self.port_var.get()
        username = self.username_var.get()
        password = self.password_var.get()

        if not url or not port or not username or not password:
            self.show_message(
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
                self.show_message(
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
                    self.show_message("Succès", "Connexion réussie!")
                    self.is_connected = True

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
                            self.show_message(
                                "Mise à jour", "Les nouveaux credentials ont été sauvegardés.")

                    self.connect_button.pack_forget()  # Cacher le bouton Connexion
                    self.load_torrent_frame.pack(side=LEFT, padx=2)
                    self.add_magnet_button.pack(side=LEFT, padx=2)
                    # unhide control_frame
                    self.control_frame.pack(side=LEFT, padx=2)
                    # Afficher le bouton Déconnecter
                    self.disconnect_button.pack(side=LEFT, padx=5)
                    self.fetch_torrents()
                else:
                    self.show_message(
                        "Erreur", "Impossible de vérifier la session. Veuillez réessayer.")
                    self.disconnect()
            else:
                self.show_message(
                    "Erreur", f"Échec de l'authentification à l'API JSON-RPC. Réponse: {data}")
                self.disconnect()
        except SSLError as e:
            self.show_message(
                "Erreur SSL", f"Erreur de certificat SSL : {str(e)}")
            self.disconnect()
            return
        except requests.RequestException as e:
            self.show_message("Erreur", f"Erreur de connexion: {str(e)}")
            self.disconnect()

    def clear_credentials(self):
        if not any(self.config['Credentials'].values()) and not self.get_password():
            self.show_message("Information", "Aucun credential à effacer.")
            return

        confirm = self.ask_yes_no(
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
            self.show_message(
                "Succès", "Tous les credentials ont été effacés.")

    def fetch_torrents(self):
        if not self.is_connected:
            self.show_message("Erreur", "Vous n'êtes pas connecté.")
            return
        # Arrêter le thread précédent s'il est en cours
        if self.update_thread and self.update_thread.is_alive():
            return
        # Lancer la mise à jour en arrière-plan
        # file deepcode ignore MissingAPI: we don't need to call join() as we are using a daemon thread that will automatically terminate when the main program ends.
        self.update_thread = threading.Thread(
            target=self.update_torrent_list_async)
        self.update_thread.start()

        self.status_label.config(text="Mise à jour en cours...")
        self.master.after(50, self.fetch_torrents_step)

    def fetch_torrents_step(self):
        try:
            response = self.session.post(self.login_url, json={
                "method": "core.get_torrents_status",
                "params": [{}, ["name", "progress", "state", "total_size", "download_payload_rate", "upload_payload_rate", "eta"]],
                "id": 2
            }, timeout=5)
            data = response.json()
            torrents = data.get('result', {})
            self.update_ui_with_torrents(torrents)
            self.status_label.config(
                text="Dernière mise à jour : " + time.strftime("%H:%M:%S"))
        except requests.RequestException as e:
            self.show_message(
                "Erreur", f"Erreur lors de la récupération des torrents: {str(e)}")
            self.status_label.config(text="Erreur lors de la mise à jour")

    def update_torrent_list_async(self):
        try:
            response = self.session.post(self.login_url, json={
                "method": "core.get_torrents_status",
                "params": [{}, ["name", "progress", "state", "total_size", "download_payload_rate", "upload_payload_rate", "eta"]],
                "id": 2
            })
            data = response.json()
            torrents = data.get('result', {})

            # Mettre à jour l'interface utilisateur dans le thread principal
            self.master.after(0, self.update_ui_with_torrents, torrents)
        except requests.RequestException as e:
            self.master.after(0, self.show_message, "Erreur",
                              f"Erreur lors de la récupération des torrents: {str(e)}")

    def update_ui_with_torrents(self, torrents):
        self.tree.delete(*self.tree.get_children())
        for index, (torrent_hash, torrent_data) in enumerate(torrents.items()):
            tags = (torrent_hash, 'evenrow' if index % 2 == 0 else 'oddrow')
            self.tree.insert('', 'end', values=(
                torrent_data['name'],
                self.format_size(torrent_data['total_size']),
                f"{torrent_data['progress']:.2f}%",
                self.format_speed(torrent_data['download_payload_rate']),
                self.format_speed(torrent_data['upload_payload_rate']),
                self.format_eta(torrent_data['eta']),
                torrent_data['state']
            ), tags=tags)

    def format_size(self, size_in_bytes):
        # Convertir les bytes en format lisible (KB, MB, GB)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} TB"

    def format_speed(self, speed_in_bytes):
        # Convertir la vitesse en format lisible (KB/s, MB/s)
        speed_in_kb = speed_in_bytes / 1024
        if speed_in_kb < 1024:
            return f"{speed_in_kb:.2f} KB/s"
        else:
            return f"{speed_in_kb/1024:.2f} MB/s"

    def format_eta(self, eta_in_seconds):
        # Convertir l'ETA en format lisible
        if eta_in_seconds == 0:
            return "Terminé"
        elif eta_in_seconds < 0:
            return "Inconnu"
        else:
            hours, remainder = divmod(eta_in_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m"

    def torrent_action(self, action):
        if not self.is_connected:
            self.show_message("Erreur", "Vous n'êtes pas connecté.")
            return
        selected_item = self.tree.selection()
        if not selected_item:
            self.show_message(
                "Avertissement", "Veuillez sélectionner un torrent.", "warning")
            return

        torrent_hash = self.tree.item(selected_item)['tags'][0]
        torrent_name = self.tree.item(selected_item)['values'][0]

        if action in ["remove", "remove_with_data"]:
            # Logique pour la suppression
            message = f"Êtes-vous sûr de vouloir supprimer le torrent '{torrent_name}'"
            if action == "remove_with_data":
                message += " et ses données associées"
            message += " ?"

            if not self.ask_yes_no("Confirmation de suppression", message):
                return

            method = "core.remove_torrent"
            params = [torrent_hash, action == "remove_with_data"]
        else:
            # Logique pour pause et resume
            method = f"core.{action}_torrent"
            params = [[torrent_hash]]

        try:
            response = self.session.post(self.login_url, json={
                "method": method,
                "params": params,
                "id": 3
            })
            data = response.json()

            if data.get('result') is not False:
                if action in ["remove", "remove_with_data"]:
                    self.show_message(
                        "Succès", f"Le torrent '{torrent_name}' a été supprimé avec succès.")
                self.fetch_torrents()  # Rafraîchir la liste des torrents
            else:
                error_msg = data.get('error', {}).get(
                    'message', 'Raison inconnue')
                self.show_message(
                    "Erreur", f"Échec de l'action '{action}'. Erreur: {error_msg}", "error")
        except requests.RequestException as e:
            self.show_message(
                "Erreur", f"Erreur lors de l'exécution de l'action: {str(e)}", "error")

    def load_torrent(self):
        if not self.is_connected:
            self.show_message("Erreur", "Vous n'êtes pas connecté.")
            return
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Torrent files", "*.torrent")])
        if file_paths:
            if len(file_paths) == 1:
                # Traitement pour un seul fichier
                file_path = file_paths[0]
                try:
                    with open(file_path, "rb") as torrent_file:
                        torrent_data = base64.b64encode(
                            torrent_file.read()).decode()

                    response = self.session.post(self.login_url, json={
                        "method": "core.add_torrent_file",
                        "params": [file_path.split("/")[-1], torrent_data, {}],
                        "id": 4
                    })
                    data = response.json()

                    if data.get('result'):
                        self.show_message(
                            "Succès", f"Torrent {file_path.split('/')[-1]} ajouté avec succès.")
                        if self.delete_torrent_var.get():
                            try:
                                os.remove(file_path)
                                self.show_message(
                                    "Information", f"Le fichier torrent {file_path} a été supprimé.")
                            except OSError as e:
                                self.show_message(
                                    "Avertissement", f"Impossible de supprimer le fichier torrent : {e}")
                    else:
                        self.show_message(
                            "Erreur", f"Échec de l'ajout du torrent. Erreur: {data.get('error')}")
                except Exception as e:
                    self.show_message(
                        "Erreur", f"Erreur lors du chargement du torrent: {str(e)}")
            else:
                # Traitement pour plusieurs fichiers
                successful_uploads = 0
                failed_uploads = 0
                files_to_delete = []

                for file_path in file_paths:
                    try:
                        with open(file_path, "rb") as torrent_file:
                            torrent_data = base64.b64encode(
                                torrent_file.read()).decode()

                        response = self.session.post(self.login_url, json={
                            "method": "core.add_torrent_file",
                            "params": [file_path.split("/")[-1], torrent_data, {}],
                            "id": 4
                        })
                        data = response.json()

                        if data.get('result'):
                            successful_uploads += 1
                            if self.delete_torrent_var.get():
                                files_to_delete.append(file_path)
                        else:
                            failed_uploads += 1
                    except Exception as e:
                        failed_uploads += 1
                        print(
                            f"Erreur lors du chargement du torrent {file_path}: {str(e)}")

                # Affichage du résumé
                message = f"{successful_uploads} torrent(s) ajouté(s) avec succès.\n"
                if failed_uploads > 0:
                    message += f"{failed_uploads} torrent(s) n'ont pas pu être ajoutés."
                self.show_message("Résumé des ajouts", message)

                # Suppression des fichiers si demandé
                if self.delete_torrent_var.get() and files_to_delete:
                    deleted_files = 0
                    for file_path in files_to_delete:
                        try:
                            os.remove(file_path)
                            deleted_files += 1
                        except OSError as e:
                            print(
                                f"Impossible de supprimer le fichier torrent {file_path}: {e}")

                    if deleted_files > 0:
                        self.show_message(
                            "Information", f"Tous les fichiers .torrent traités ({deleted_files}) ont été effacés.")

            self.fetch_torrents()

    def add_magnet(self):
        if not self.is_connected:
            self.show_message("Erreur", "Vous n'êtes pas connecté.")
            return
        magnet_link = tk.simpledialog.askstring(
            "Ajouter un magnet", "Collez le lien magnet ici:")
        if magnet_link:
            try:
                response = self.session.post(self.login_url, json={
                    "method": "core.add_torrent_magnet",
                    "params": [magnet_link, {}],
                    "id": 5
                })
                data = response.json()

                if data.get('result'):
                    self.show_message("Succès", "Magnet ajouté avec succès.")
                    self.fetch_torrents()
                else:
                    self.show_message(
                        "Erreur", f"Échec de l'ajout du magnet. Erreur: {data.get('error')}")
            except Exception as e:
                self.show_message(
                    "Erreur", f"Erreur lors de l'ajout du magnet: {str(e)}")

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
