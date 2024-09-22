import requests
from torrents_updater import fetch_torrents
from ui_utils import center_dialog, show_message, ask_yes_no
import tkinter as tk
from tkinter import ttk
import platform
from localization import _


def execute_api_call(self, method, params):
    try:
        response = self.session.post(self.login_url, json={
            "method": method,
            "params": params,
            "id": 3
        })
        data = response.json()

        if data.get('result') is not False:
            return True
        else:
            error_msg = data.get('error', {}).get(
                'message', _('Unknown reason'))
            show_message(self.master, _("Error"), _(
                "Action failed. Error: {}").format(error_msg), "error")
            return False
    except requests.RequestException as e:
        show_message(self.master, _("Error"), _(
            "Error executing action: {}").format(str(e)), "error")
        return False


def handle_pause_resume_action(self, action, torrents):
    if action == "pause":
        to_process = [t for t in torrents if t['state']
                      not in [_("Paused"), _("Pausing")]]
        already_processed = [
            t for t in torrents if t['state'] in [_("Paused"), _("Pausing")]]
        desired_state = _("paused")
    else:  # resume
        to_process = [t for t in torrents if t['state']
                      in [_("Paused"), _("Pausing")]]
        already_processed = [t for t in torrents if t['state']
                             not in [_("Paused"), _("Pausing")]]
        desired_state = _("resumed")

    if not to_process:
        if len(torrents) == 1:
            show_message(self.master, _("Information"), _(
                "The torrent '{}' is already {}").format(torrents[0]['name'], desired_state))
        else:
            show_message(self.master, _("Information"), _(
                "All selected torrents are already {}").format(desired_state))
        return

    method = f"core.{action}_torrents"
    params = [[t['hash'] for t in to_process]]

    if execute_api_call(self, method, params):
        if len(torrents) == 1:
            show_message(self.master, _("Success"), _(
                "The torrent '{}' has been {}").format(torrents[0]['name'], desired_state))
        else:
            message = _("{} torrent(s) have been {}").format(
                len(to_process), desired_state)
            if already_processed:
                message += _("\n{} torrent(s) were already in the appropriate state").format(
                    len(already_processed))
            show_message(self.master, _("Success"), message)
        fetch_torrents(self)


def handle_remove_action(self, action, torrents):
    message = _("Are you sure you want to remove {} torrent(s)").format(
        len(torrents))
    if action == "remove_with_data":
        message += _(" and their associated data")
    message += "?"

    if not ask_yes_no(self.master, _("Deletion confirmation"), message):
        return

    method = "core.remove_torrents"
    params = [[t['hash'] for t in torrents], action == "remove_with_data"]

    if execute_api_call(self, method, params):
        show_message(self.master, _("Success"), _(
            "{} torrent(s) have been successfully removed").format(len(torrents)))
        fetch_torrents(self)


def handle_other_actions(self, action, torrents):
    method = f"core.{action}_torrents"
    params = [[t['hash'] for t in torrents]]

    if execute_api_call(self, method, params):
        if len(torrents) == 1:
            show_message(self.master, _("Success"), _(
                "The action '{}' has been performed on the torrent '{}'").format(action, torrents[0]['name']))
        else:
            show_message(self.master, _("Success"), _(
                "The action '{}' has been performed on {} torrents").format(action, len(torrents)))
        fetch_torrents(self)


def show_torrent_context_menu(self, event):
    # Vérifier si c'est un clic droit (Button-2 sur Mac, Button-3 sur d'autres systèmes)
    if (platform.system() == 'Darwin' and event.num == 2) or (platform.system() != 'Darwin' and event.num == 3):
        # Sélectionner l'item sous le curseur si ce n'est pas déjà fait
        item = self.tree.identify_row(event.y)
        if not item:
            return

        if item not in self.tree.selection():
            self.tree.selection_set(item)

        # Créer le menu contextuel
        context_menu = tk.Menu(self.master, tearoff=0)

        # Récupérer l'état actuel du torrent
        item_values = self.tree.item(item)['values']
        current_state = item_values[6] if len(item_values) > 6 else ""

        # Ajouter les options du menu en fonction de l'état actuel
        if current_state in [_("Paused"), _("Pausing")]:
            context_menu.add_command(
                label=_("Resume"), command=lambda: self.torrent_action("resume"))
        else:
            context_menu.add_command(
                label=_("Pause"), command=lambda: self.torrent_action("pause"))

        context_menu.add_separator()
        context_menu.add_command(
            label=_("Remove"), command=lambda: self.torrent_action("remove"))
        context_menu.add_command(label=_(
            "Remove with data"), command=lambda: self.torrent_action("remove_with_data"))
        context_menu.add_separator()
        context_menu.add_command(label=_("Edit Tracker"),
                                 command=lambda: edit_tracker(self))
        # Afficher le menu à la position du clic
        context_menu.tk_popup(event.x_root, event.y_root)


def edit_tracker(self):
    selected_items = self.tree.selection()
    if not selected_items:
        show_message(self.master, _("Warning"), _(
            "Please select at least one torrent."), "warning")
        return

    # Récupérer le tracker actuel du premier torrent sélectionné
    torrent_hash = self.tree.item(selected_items[0])['tags'][0]
    current_tracker = get_current_tracker(self, torrent_hash)

    # Créer une fenêtre modale pour l'édition du tracker
    dialog = tk.Toplevel(self.master)
    dialog.title(_("Edit Tracker"))
    dialog.geometry("600x150")
    dialog.resizable(False, False)
    dialog.transient(self.master)
    dialog.grab_set()

    frame = ttk.Frame(dialog, padding="20 20 20 20")
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text=_("Enter new tracker address:")
              ).pack(anchor="w", pady=(0, 5))

    tracker_var = tk.StringVar(value=current_tracker)
    entry = ttk.Entry(frame, textvariable=tracker_var, width=50)
    entry.pack(fill=tk.X, pady=(0, 10))

    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))

    def on_submit():
        new_tracker = tracker_var.get().strip()
        if new_tracker:
            success = update_trackers(self, selected_items, new_tracker)
            if success:
                show_message(self.master, _("Success"), _(
                    "Tracker updated successfully."))
                dialog.destroy()
                fetch_torrents(self)  # Rafraîchir la liste des torrents
            else:
                show_message(self.master, _("Error"),
                             _("Failed to update tracker."))
        else:
            show_message(self.master, _("Error"), _(
                "Please enter a valid tracker address."))

    ttk.Button(button_frame, text=_("Update"), command=on_submit,
               style='success.TButton').pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(button_frame, text=_("Cancel"), command=dialog.destroy,
               style='danger.TButton').pack(side=tk.LEFT)

    center_dialog(dialog, self.master)


def get_current_tracker(self, torrent_hash):
    response = self.session.post(self.login_url, json={
        "method": "core.get_torrent_status",
        "params": [torrent_hash, ["trackers"]],
        "id": 1
    })
    data = response.json()
    trackers = data.get('result', {}).get('trackers', [])
    if trackers:
        return trackers[0]['url']
    return ''


def update_trackers(self, torrent_items, new_tracker):
    for item in torrent_items:
        torrent_hash = self.tree.item(item)['tags'][0]
        response = self.session.post(self.login_url, json={
            "method": "core.set_torrent_trackers",
            "params": [torrent_hash, [{"url": new_tracker, "tier": 0}]],
            "id": 1
        })
        if not response.json().get('result'):
            return False
    return True
