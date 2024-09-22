import os
import base64
import re
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from torrents_updater import fetch_torrents
from ui_utils import center_dialog, show_message, ask_yes_no
from localization import _


def load_torrent(self):
    if not self.is_connected:
        show_message(self.master, _("Error"), _("You are not connected."))
        return
    file_paths = filedialog.askopenfilenames(
        filetypes=[(_("Torrent files"), "*.torrent")])
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
            show_message(self.master, _("Success"), _(
                "Torrent {} added successfully.").format(file_path.split('/')[-1]))
            if self.delete_torrent_var.get():
                try:
                    os.remove(file_path)
                    show_message(self.master, _("Information"), _(
                        "The torrent file {} has been deleted.").format(file_path))
                except OSError as e:
                    show_message(self.master, _("Warning"), _(
                        "Unable to delete torrent file: {}").format(e))
        else:
            error = data.get('error', {})
            if isinstance(error, dict) and 'message' in error:
                if "Torrent already in session" in error['message']:
                    show_message(self.master, _("Information"), _(
                        "The torrent {} already exists in the session.").format(file_path.split('/')[-1]))
                else:
                    show_message(self.master, _("Error"), _(
                        "Failed to add torrent. Error: {}").format(error['message']))
            else:
                show_message(self.master, _("Error"), _(
                    "Failed to add torrent. Unknown error."))
    except Exception as e:
        show_message(self.master, _("Error"), _(
            "Error loading torrent: {}").format(str(e)))


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
                                continue_warnings = ask_yes_no(self.master, _("Duplicate detected"),
                                                               _("The torrent {} already exists.\n\nDo you want to continue being notified for subsequent duplicates?").format(file_path.split('/')[-1]))
                                if not continue_warnings:
                                    warn_for_duplicates = False
                            else:
                                add_anyway = ask_yes_no(self.master, _("Duplicate detected"),
                                                        _("The torrent {} already exists. Do you want to add it anyway?").format(file_path.split('/')[-1]))
                                if add_anyway:
                                    successful_uploads += 1
                                    continue
                        already_existing += 1
                    else:
                        failed_uploads += 1
                else:
                    failed_uploads += 1
        except Exception as e:
            failed_uploads += 1
            print(_("Error loading torrent {}: {}").format(file_path, str(e)))

    message = _("{} torrent(s) added successfully.\n").format(
        successful_uploads)
    if already_existing > 0:
        message += _("{} torrent(s) already existing in the session.\n").format(already_existing)
    if failed_uploads > 0:
        message += _("{} torrent(s) could not be added.").format(failed_uploads)
    show_message(self.master, _("Add Summary"), message)

    if self.delete_torrent_var.get() and files_to_delete:
        delete_torrent_files(self, files_to_delete)


def delete_torrent_files(self, files_to_delete):
    deleted_files = 0
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            deleted_files += 1
        except OSError as e:
            print(_("Unable to delete torrent file {}: {}").format(file_path, e))

    if deleted_files > 0:
        show_message(self.master, _("Information"), _(
            "All processed .torrent files ({}) have been deleted.").format(deleted_files))


def add_magnet(self):
    if not self.is_connected:
        show_message(self.master, _("Error"), _("You are not connected."))
        return

    dialog = tk.Toplevel(self.master)
    dialog.title(_("Add Magnet"))
    dialog.geometry("500x200")
    dialog.minsize(500, 200)
    dialog.resizable(True, True)

    dialog.transient(self.master)
    dialog.grab_set()

    frame = ttk.Frame(dialog, padding="20 20 20 20")
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text=_("Paste the magnet link here:"), font=(
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
                show_message(self.master, _("Error"), _(
                    "The clipboard content is not a valid magnet link."))
        except tk.TclError:
            show_message(self.master, _("Error"), _(
                "The clipboard is empty or its content is not accessible."))

    def on_submit():
        magnet_link = magnet_var.get().strip()
        if magnet_link and is_valid_magnet(magnet_link):
            dialog.destroy()
            process_magnet_link(self, magnet_link)
        else:
            show_message(self.master, _("Error"), _(
                "Please enter a valid magnet link."))

    ttk.Button(button_frame, text=_("Paste"), command=paste_clipboard,
               style='info.TButton').pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(button_frame, text=_("Add"), command=on_submit,
               style='success.TButton').pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(button_frame, text=_("Cancel"), command=dialog.destroy,
               style='danger.TButton').pack(side=tk.LEFT)

    dialog.after(10, lambda: center_dialog(dialog, self.master))

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
            show_message(self.master, _("Success"),
                         _("Magnet added successfully."))
            fetch_torrents(self)
        else:
            error = data.get('error', {})
            if isinstance(error, dict) and 'message' in error:
                if "Torrent already in session" in error['message']:
                    show_message(self.master, _("Information"), _(
                        "This magnet already exists in the session."))
                else:
                    show_message(self.master, _("Error"), _(
                        "Failed to add magnet. Error: {}").format(error['message']))
            else:
                show_message(self.master, _("Error"), _(
                    "Failed to add magnet. Unknown error."))
    except Exception as e:
        show_message(self.master, _("Error"), _(
            "Error adding magnet: {}").format(str(e)))
