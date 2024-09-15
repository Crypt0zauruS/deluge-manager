import os
import base64
import re
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from torrents_updater import fetch_torrents
from ui_utils import center_dialog, show_message, ask_yes_no


def load_torrent(self):
    if not self.is_connected:
        show_message(self.master, "Erreur", "Vous n'êtes pas connecté.")
        return
    file_paths = filedialog.askopenfilenames(
        filetypes=[("Torrent files", "*.torrent")])
    if file_paths:
        if len(file_paths) == 1:
            process_single_torrent(self, file_paths[0])
        else:
            process_multiple_torrents(self, file_paths)
        fetch_torrents(self)


def process_single_torrent(self, file_path):
    try:
        with open(file_path, "rb") as torrent_file:
            torrent_data = base64.b64encode(torrent_file.read()).decode()

        response = self.session.post(self.login_url, json={
            "method": "core.add_torrent_file",
            "params": [file_path.split("/")[-1], torrent_data, {}],
            "id": 4
        })
        data = response.json()

        if data.get('result'):
            show_message(self.master, "Succès", f"Torrent {
                         file_path.split('/')[-1]} ajouté avec succès.")
            if self.delete_torrent_var.get():
                try:
                    os.remove(file_path)
                    show_message(self.master, "Information", f"Le fichier torrent {
                                 file_path} a été supprimé.")
                except OSError as e:
                    show_message(self.master, "Avertissement",
                                 f"Impossible de supprimer le fichier torrent : {e}")
        else:
            error = data.get('error', {})
            if isinstance(error, dict) and 'message' in error:
                if "Torrent already in session" in error['message']:
                    show_message(self.master, "Information", f"Le torrent {
                                 file_path.split('/')[-1]} existe déjà dans la session.")
                else:
                    show_message(self.master, "Erreur", f"Échec de l'ajout du torrent. Erreur: {
                                 error['message']}")
            else:
                show_message(self.master, "Erreur",
                             f"Échec de l'ajout du torrent. Erreur inconnue.")
    except Exception as e:
        show_message(self.master, "Erreur",
                     f"Erreur lors du chargement du torrent: {str(e)}")


def process_multiple_torrents(self, file_paths):
    successful_uploads = 0
    failed_uploads = 0
    already_existing = 0
    files_to_delete = []
    warn_for_duplicates = True
    first_duplicate_encountered = False

    for file_path in file_paths:
        try:
            with open(file_path, "rb") as torrent_file:
                torrent_data = base64.b64encode(torrent_file.read()).decode()

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
                error = data.get('error', {})
                if isinstance(error, dict) and 'message' in error:
                    if "Torrent already in session" in error['message']:
                        if warn_for_duplicates:
                            if not first_duplicate_encountered:
                                first_duplicate_encountered = True
                                continue_warnings = ask_yes_no(self.master, "Doublon détecté",
                                                               f"Le torrent {file_path.split(
                                                                   '/')[-1]} existe déjà.\n\n"
                                                               "Voulez-vous continuer à être averti pour les doublons suivants ?")
                                if not continue_warnings:
                                    warn_for_duplicates = False
                            else:
                                add_anyway = ask_yes_no(self.master, "Doublon détecté",
                                                        f"Le torrent {file_path.split('/')[-1]} existe déjà. Voulez-vous l'ajouter quand même ?")
                                if add_anyway:
                                    # Ici, vous pouvez ajouter le code pour forcer l'ajout du torrent si nécessaire
                                    successful_uploads += 1
                                    continue
                        already_existing += 1
                    else:
                        failed_uploads += 1
                else:
                    failed_uploads += 1
        except Exception as e:
            failed_uploads += 1
            print(f"Erreur lors du chargement du torrent {
                  file_path}: {str(e)}")

    message = f"{successful_uploads} torrent(s) ajouté(s) avec succès.\n"
    if already_existing > 0:
        message += f"{
            already_existing} torrent(s) déjà existant(s) dans la session.\n"
    if failed_uploads > 0:
        message += f"{failed_uploads} torrent(s) n'ont pas pu être ajoutés."
    show_message(self.master, "Résumé des ajouts", message)

    if self.delete_torrent_var.get() and files_to_delete:
        delete_torrent_files(self, files_to_delete)


def delete_torrent_files(self, files_to_delete):
    deleted_files = 0
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            deleted_files += 1
        except OSError as e:
            print(f"Impossible de supprimer le fichier torrent {
                  file_path}: {e}")

    if deleted_files > 0:
        show_message(self.master, "Information", f"Tous les fichiers .torrent traités ({
            deleted_files}) ont été effacés.")


def add_magnet(self):
    if not self.is_connected:
        show_message(self.master, "Erreur", "Vous n'êtes pas connecté.")
        return

    dialog = tk.Toplevel(self.master)
    dialog.title("Ajouter un magnet")
    dialog.geometry("500x200")
    dialog.minsize(500, 200)
    dialog.resizable(True, True)

    # Rendre la fenêtre modale
    dialog.transient(self.master)
    dialog.grab_set()

    frame = ttk.Frame(dialog, padding="20 20 20 20")
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Collez le lien magnet ici :", font=(
        "TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 10))

    magnet_var = tk.StringVar()
    entry = ttk.Entry(frame, textvariable=magnet_var, width=60)
    entry.pack(fill=tk.X, expand=True, pady=(0, 10))

    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))

    def paste_clipboard():
        try:
            clipboard_content = dialog.clipboard_get()
            if is_valid_magnet(clipboard_content):
                magnet_var.set(clipboard_content)
            else:
                show_message(self.master,
                             "Erreur", "Le contenu du presse-papiers n'est pas un lien magnet valide.")
        except tk.TclError:
            show_message(self.master,
                         "Erreur", "Le presse-papiers est vide ou son contenu n'est pas accessible.")

    def on_submit():
        magnet_link = magnet_var.get().strip()
        if magnet_link and is_valid_magnet(magnet_link):
            dialog.destroy()
            process_magnet_link(self, magnet_link)
        else:
            show_message(self.master,
                         "Erreur", "Veuillez entrer un lien magnet valide.")

    ttk.Button(button_frame, text="Coller", command=paste_clipboard,
               style='info.TButton').pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(button_frame, text="Ajouter", command=on_submit,
               style='success.TButton').pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(button_frame, text="Annuler", command=dialog.destroy,
               style='danger.TButton').pack(side=tk.LEFT)

    # Centrer la boîte de dialogue
    dialog.after(10, lambda: center_dialog(dialog, self.master))

    # Attendre que la fenêtre soit fermée
    self.master.wait_window(dialog)


def is_valid_magnet(link):
    magnet_pattern = r'^magnet:\?xt=urn:btih:[a-fA-F0-9]{40}.*$'
    return re.match(magnet_pattern, link) is not None


def process_magnet_link(self, magnet_link):
    try:
        response = self.session.post(self.login_url, json={
            "method": "core.add_torrent_magnet",
            "params": [magnet_link, {}],
            "id": 5
        })
        data = response.json()

        if data.get('result'):
            show_message(self.master, "Succès", "Magnet ajouté avec succès.")
            fetch_torrents(self)
        else:
            error = data.get('error', {})
            if isinstance(error, dict) and 'message' in error:
                if "Torrent already in session" in error['message']:
                    show_message(self.master, "Information",
                                 "Ce magnet existe déjà dans la session.")
                else:
                    show_message(self.master, "Erreur", f"Échec de l'ajout du magnet. Erreur: {
                                 error['message']}")
            else:
                show_message(self.master, "Erreur",
                             "Échec de l'ajout du magnet. Erreur inconnue.")
    except Exception as e:
        show_message(self.master,
                     "Erreur", f"Erreur lors de l'ajout du magnet: {str(e)}")
