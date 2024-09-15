import requests
from torrents_updater import fetch_torrents
from ui_utils import show_message, ask_yes_no


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
            error_msg = data.get('error', {}).get('message', 'Raison inconnue')
            show_message(self.master, "Erreur", f"Échec de l'action. Erreur: {
                error_msg}", "error")
            return False
    except requests.RequestException as e:
        show_message(self.master, "Erreur", f"Erreur lors de l'exécution de l'action: {
            str(e)}", "error")
        return False


def handle_pause_resume_action(self, action, torrents):
    if action == "pause":
        to_process = [t for t in torrents if t['state']
                      not in ["Paused", "Pausing"]]
        already_processed = [
            t for t in torrents if t['state'] in ["Paused", "Pausing"]]
        desired_state = "en pause"
    else:  # resume
        to_process = [t for t in torrents if t['state']
                      in ["Paused", "Pausing"]]
        already_processed = [
            t for t in torrents if t['state'] not in ["Paused", "Pausing"]]
        desired_state = "repris"

    if not to_process:
        if len(torrents) == 1:
            show_message(self.master, "Information", f"Le torrent '{
                torrents[0]['name']}' est déjà {desired_state}.")
        else:
            show_message(self.master,
                         "Information", f"Tous les torrents sélectionnés sont déjà {desired_state}.")
        return

    method = f"core.{action}_torrents"
    params = [[t['hash'] for t in to_process]]

    if execute_api_call(self, method, params):
        if len(torrents) == 1:
            show_message(self.master, "Succès", f"Le torrent '{
                torrents[0]['name']}' a été {desired_state}.")
        else:
            message = f"{len(to_process)} torrent(s) ont été {desired_state}."
            if already_processed:
                message += f"\n{len(already_processed)
                                } torrent(s) étaient déjà dans l'état approprié."
            show_message(self.master, "Succès", message)
        fetch_torrents(self)


def handle_remove_action(self, action, torrents):
    message = f"Êtes-vous sûr de vouloir supprimer {len(torrents)} torrent(s)"
    if action == "remove_with_data":
        message += " et leurs données associées"
    message += " ?"

    if not ask_yes_no(self.master, "Confirmation de suppression", message):
        return

    method = "core.remove_torrents"
    params = [[t['hash'] for t in torrents], action == "remove_with_data"]

    if execute_api_call(self, method, params):
        show_message(self.master,
                     "Succès", f"{len(torrents)} torrent(s) ont été supprimés avec succès.")
        fetch_torrents(self)


def handle_other_actions(self, action, torrents):
    method = f"core.{action}_torrents"
    params = [[t['hash'] for t in torrents]]

    if execute_api_call(self, method, params):
        if len(torrents) == 1:
            show_message(self.master, "Succès", f"L'action '{
                action}' a été effectuée sur le torrent '{torrents[0]['name']}'.")
        else:
            show_message(self.master, "Succès", f"L'action '{action}' a été effectuée sur {
                len(torrents)} torrents.")
        fetch_torrents(self)
