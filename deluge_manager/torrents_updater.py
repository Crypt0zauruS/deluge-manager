from ui_settings import get_color_for_progress
import threading
import time
import requests
from ui_utils import show_message, format_size, format_speed, format_eta
from localization import _
import concurrent.futures


TIMEOUT_SECONDS = 10


def fetch_torrents(self):
    if not self.is_connected:
        show_message(self.master, _("Error"), _("You are not connected."))
        return

    if hasattr(self, 'update_thread') and isinstance(self.update_thread, threading.Thread) and self.update_thread.is_alive():
        return

    self.update_thread = threading.Thread(
        target=update_torrent_list_async, args=(self,))
    self.update_thread.daemon = True
    self.update_thread.start()

    self.status_label.config(text=_("Update in progress..."))
    self.master.after(50, lambda: fetch_torrents_step(self))


def fetch_torrents_step(self):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(fetch_torrents_data, self)
        try:
            torrents = future.result(timeout=TIMEOUT_SECONDS)
            update_ui_with_torrents(self, torrents)
            self.status_label.config(
                text=_("Last manual update:") + time.strftime("%H:%M:%S"))
            self.update_job = self.master.after(
                5000, lambda: update_torrents(self))
        except concurrent.futures.TimeoutError:
            # Give the thread a chance to exit
            self.update_thread.join(timeout=0.1)
            show_message(self.master, _("Error"), _(
                "Request timed out. Please try again later."))
            self.status_label.config(text=_("Update timed out"))
        except Exception as e:
            show_message(self.master,
                         _("Error"), _("Error retrieving torrents: {}").format(str(e)))
            self.status_label.config(text=_("Error during update"))


def fetch_torrents_data(self):
    response = self.session.post(self.login_url, json={
        "method": "core.get_torrents_status",
        "params": [{}, ["name", "progress", "state", "total_size", "download_payload_rate", "upload_payload_rate", "eta"]],
        "id": 2
    }, timeout=TIMEOUT_SECONDS)
    data = response.json()
    return data.get('result', {})


def update_torrent_list_async(self):
    try:
        torrents = fetch_torrents_data(self)
        self.master.after(0, lambda: update_ui_with_torrents(self, torrents))
    except requests.RequestException as e:
        self.master.after(0, lambda: show_message(self.master,
                                                  _("Error"), _("Error retrieving torrents: {}").format(str(e))))
    finally:
        self.update_thread = None


def update_ui_with_torrents(self, torrents):
    selected_items = self.tree.selection()
    self.tree.delete(*self.tree.get_children())
    for index, (torrent_hash, torrent_data) in enumerate(torrents.items()):
        tags = [torrent_hash]
        if torrent_data['state'] == _('Downloading'):
            tags.append('downloading')
        elif torrent_data['state'] == _('Error'):
            tags.append('error')
        else:
            tags.append('evenrow' if index % 2 == 0 else 'oddrow')

        item_id = self.tree.insert('', 'end', values=(
            torrent_data['name'],
            format_size(torrent_data['total_size']),
            f"{torrent_data['progress']:.2f}%",
            format_speed(torrent_data['download_payload_rate']),
            format_speed(torrent_data['upload_payload_rate']),
            format_eta(torrent_data['eta']),
            _(torrent_data['state'])
        ), tags=tags)
        if torrent_hash in selected_items:
            self.tree.selection_add(item_id)

    self.tree.tag_configure('downloading', background='#D3D3D3')
    self.tree.tag_configure(
        'error', background='orangered', foreground='black')


def update_torrents(self):
    if not self.is_connected or not self.session:
        return

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(fetch_torrents_data, self)
        try:
            torrents = future.result(timeout=TIMEOUT_SECONDS)
            base_color = self.config.get(
                'Settings', 'download_color', fallback='#D3D3D3')

            for torrent_hash, torrent_data in torrents.items():
                item = next((item for item in self.tree.get_children()
                            if torrent_hash in self.tree.item(item, 'tags')), None)
                if item:
                    progress = torrent_data['progress']
                    state = torrent_data['state']

                    if state == 'Downloading':
                        bg_color = get_color_for_progress(progress, base_color)
                        tag_name = f'downloading_{torrent_hash}'
                        self.tree.tag_configure(
                            tag_name, background=bg_color, foreground='black')
                        self.tree.item(item, tags=[torrent_hash, tag_name])
                    elif state == 'Error':
                        self.tree.item(item, tags=[torrent_hash, 'error'])
                    else:
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
                        _(state)
                    ))

            self.update_job = self.master.after(
                5000, lambda: update_torrents(self))
        except concurrent.futures.TimeoutError:
            print("Update timed out")
            self.update_job = self.master.after(
                5000, lambda: update_torrents(self))
        except Exception as e:
            show_message(self.master,
                         _("Error"), _("Error updating torrents: {}").format(str(e)))
            self.update_job = self.master.after(
                5000, lambda: update_torrents(self))
