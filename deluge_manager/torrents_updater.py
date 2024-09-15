import threading
import time
import requests
from ui_utils import show_message, format_size, format_speed, format_eta


def fetch_torrents(self):
    if not self.is_connected:
        show_message(self.master, "Erreur", "Vous n'êtes pas connecté.")
        return
    # Arrêter le thread précédent s'il est en cours
    if self.update_thread and self.update_thread.is_alive():
        return
    # Lancer la mise à jour en arrière-plan
    # file deepcode ignore MissingAPI: we don't need to call join() as we are using a daemon thread
    # that will automatically terminate when the main program ends.
    self.update_thread = threading.Thread(
        target=update_torrent_list_async, args=(self,))
    self.update_thread.daemon = True
    self.update_thread.start()

    self.status_label.config(text="Mise à jour en cours...")
    self.master.after(50, lambda: fetch_torrents_step(self))


def fetch_torrents_step(self):
    try:
        response = self.session.post(self.login_url, json={
            "method": "core.get_torrents_status",
            "params": [{}, ["name", "progress", "state", "total_size", "download_payload_rate", "upload_payload_rate", "eta"]],
            "id": 2
        }, timeout=5)
        data = response.json()
        torrents = data.get('result', {})
        update_ui_with_torrents(self, torrents)
        self.status_label.config(
            text="Dernière mise à jour manuelle : " + time.strftime("%H:%M:%S"))
        self.update_job = self.master.after(
            5000, lambda: update_torrents(self))
    except requests.RequestException as e:
        show_message(self.master,
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
        self.master.after(0, lambda: update_ui_with_torrents(self, torrents))
    except requests.RequestException as e:
        self.master.after(0, lambda: show_message(self.master,
                                                  "Erreur", f"Erreur lors de la récupération des torrents: {str(e)}"))


def update_ui_with_torrents(self, torrents):
    selected_items = self.tree.selection()
    self.tree.delete(*self.tree.get_children())
    for index, (torrent_hash, torrent_data) in enumerate(torrents.items()):
        tags = [torrent_hash]
        if torrent_data['state'] == 'Downloading':
            tags.append('downloading')
        else:
            tags.append('evenrow' if index % 2 == 0 else 'oddrow')

        item_id = self.tree.insert('', 'end', values=(
            torrent_data['name'],
            format_size(torrent_data['total_size']),
            f"{torrent_data['progress']:.2f}%",
            format_speed(torrent_data['download_payload_rate']),
            format_speed(torrent_data['upload_payload_rate']),
            format_eta(torrent_data['eta']),
            torrent_data['state']
        ), tags=tags)
        if torrent_hash in selected_items:
            self.tree.selection_add(item_id)

    # Configure la couleur pour les torrents en téléchargement
    self.tree.tag_configure('downloading', background='#D3D3D3')


def update_torrents(self):
    if not self.is_connected or not self.session:
        return
    try:
        response = self.session.post(self.login_url, json={
            "method": "core.get_torrents_status",
            "params": [{}, ["name", "progress", "state", "total_size", "download_payload_rate", "upload_payload_rate", "eta"]],
            "id": 2
        }, timeout=5)
        data = response.json()
        torrents = data.get('result', {})

        for torrent_hash, torrent_data in torrents.items():
            item = next((item for item in self.tree.get_children()
                        if torrent_hash in self.tree.item(item, 'tags')), None)
            if item:
                progress = torrent_data['progress']
                state = torrent_data['state']

                if state == 'Downloading':
                    bg_color = get_color_for_progress(progress)
                    tag_name = f'downloading_{torrent_hash}'
                    self.tree.tag_configure(
                        tag_name, background=bg_color, foreground='black')
                    self.tree.item(item, tags=[torrent_hash, tag_name])
                else:
                    # Réinitialiser la couleur pour les torrents non en téléchargement
                    row_type = 'evenrow' if int(
                        self.tree.index(item)) % 2 == 0 else 'oddrow'
                    self.tree.item(item, tags=[torrent_hash, row_type])

                self.tree.item(item, values=(
                    torrent_data['name'],
                    format_size(torrent_data['total_size']),
                    f"{progress:.2f}%",
                    format_speed(torrent_data['download_payload_rate']),
                    format_speed(torrent_data['upload_payload_rate']),
                    format_eta(torrent_data['eta']),
                    state
                ))

        self.update_job = self.master.after(
            5000, lambda: update_torrents(self))
    except requests.RequestException as e:
        show_message(self.master,
                     "Erreur", f"Erreur lors de la mise à jour des torrents: {str(e)}")


def get_color_for_progress(progress, color_scheme='blue'):
    if color_scheme == 'blue':
        # Progression vers le bleu
        r = 211 - int((211 - 30) * progress / 100)  # De 211 à 30
        g = 211 - int((211 - 144) * progress / 100)  # De 211 à 144
        b = 211 + int((255 - 211) * progress / 100)  # De 211 à 255
    elif color_scheme == 'green':
        # Progression vers le vert
        r = 211 - int((211 - 76) * progress / 100)  # De 211 à 76
        g = 211 + int((255 - 211) * progress / 100)  # De 211 à 255
        b = 211 - int((211 - 76) * progress / 100)  # De 211 à 76
    else:
        # Fallback sur le gris si une option non valide est spécifiée
        r = g = b = 211

    return f'#{r:02x}{g:02x}{b:02x}'
