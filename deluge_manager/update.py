import requests
import platform
import os
import tkinter as tk
from tkinter import ttk
from ui_utils import show_message, version, author, repo_name, center_dialog
from localization import _
import threading
import json
import time

home_dir = os.path.expanduser("~")
download_dir = os.path.join(home_dir, "Downloads")
temp_dir = os.path.join(download_dir, ".temp")

MAX_RETRIES = 5
RETRY_DELAY = 5
TIMEOUT = 10


def is_newer_version(current_version, latest_version):
    def version_tuple(version):
        # Remove all characters before and after version numbers
        version = ''.join(filter(lambda x: x.isdigit() or x == '.', version))
        return tuple(map(int, (version.split("."))))

    current_version_tuple = version_tuple(current_version)
    latest_version_tuple = version_tuple(latest_version)

    return latest_version_tuple > current_version_tuple


def get_download_state(filename):
    resume_info_path = os.path.join(temp_dir, f"{filename}.json")
    if os.path.exists(resume_info_path):
        with open(resume_info_path, 'r') as f:
            return json.load(f)
    return None


def save_download_state(filename, state):
    resume_info_path = os.path.join(temp_dir, f"{filename}.json")
    with open(resume_info_path, 'w') as f:
        json.dump(state, f)


def remove_download_state(filename):
    resume_info_path = os.path.join(temp_dir, f"{filename}.json")
    temp_file_path = os.path.join(temp_dir, f"{filename}.part")
    if os.path.exists(resume_info_path):
        os.remove(resume_info_path)
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


def download_file(self, download_url, progress_var, cancel_download, pause_download, dialog):
    def get_filename_from_url():
        return download_url.split("/")[-1]

    filename = get_filename_from_url()
    file_path = os.path.join(download_dir, filename)
    temp_file_path = os.path.join(temp_dir, f"{filename}.part")

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    download_state = get_download_state(filename)
    downloaded_size = download_state['downloaded_size'] if download_state else 0
    headers = {'Range': f'bytes={
        downloaded_size}-'} if downloaded_size > 0 else {}

    retries = 0
    while retries < MAX_RETRIES and not cancel_download.get():
        try:
            with requests.get(download_url, stream=True, headers=headers, timeout=TIMEOUT) as response:
                response.raise_for_status()
                total_size = int(response.headers.get(
                    'content-length', 0)) + downloaded_size

                mode = 'ab' if downloaded_size > 0 else 'wb'
                with open(temp_file_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            if cancel_download.get():
                                raise Exception("Download cancelled")

                            if pause_download.get():
                                save_download_state(
                                    filename, {'downloaded_size': downloaded_size})
                                return "paused"

                            f.write(chunk)
                            downloaded_size += len(chunk)
                            progress = (downloaded_size / total_size) * 100
                            progress_var.set(progress)
                            self.master.update_idletasks()

                            if downloaded_size % (1024 * 1024) == 0:  # Every 1 MB
                                save_download_state(
                                    filename, {'downloaded_size': downloaded_size})

                # Download completed successfully
                os.replace(temp_file_path, file_path)
                remove_download_state(filename)
                return "completed"

        except requests.RequestException as e:
            retries += 1
            if retries < MAX_RETRIES and not cancel_download.get():
                show_message(self.master, _("Connection Error"),
                             _(f'Connection lost. Retrying in {RETRY_DELAY} seconds... (Attempt {retries}/{MAX_RETRIES})'))
                time.sleep(RETRY_DELAY)
                headers = {'Range': f'bytes={downloaded_size}-'}
            else:
                if cancel_download.get():
                    remove_download_state(filename)
                    return "cancelled"
                else:
                    save_download_state(
                        filename, {'downloaded_size': downloaded_size})
                    return "failed"

        except Exception as e:
            if str(e) == "Download cancelled":
                remove_download_state(filename)
                return "cancelled"
            else:
                save_download_state(
                    filename, {'downloaded_size': downloaded_size})
                return "failed"

    return "failed"


def ask_download(self, title, message, download_url=None):
    dialog = tk.Toplevel(self.master)
    dialog.title(title)
    dialog.geometry("400x250")
    dialog.minsize(400, 250)
    dialog.resizable(True, True)

    dialog.transient(self.master)
    dialog.grab_set()

    frame = ttk.Frame(dialog, padding="20 20 20 20")
    frame.pack(fill=tk.BOTH, expand=True)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill=tk.X, pady=(20, 10))

    icon_label = ttk.Label(frame, text="❓", font=("TkDefaultFont", 48))
    icon_label.pack(pady=(0, 10))

    message_label = ttk.Label(
        frame, text=message, wraplength=360, justify="center")
    message_label.pack(expand=True)

    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=10)

    cancel_download = tk.BooleanVar(value=False)
    pause_download = tk.BooleanVar(value=False)

    filename = download_url.split("/")[-1]
    download_state = get_download_state(filename)

    def on_start_download():
        nonlocal download_thread
        if download_url is not None:
            download_thread = threading.Thread(
                target=download_and_update_ui,
                args=(self, download_url, progress_var,
                      cancel_download, pause_download, dialog)
            )
            download_thread.daemon = True
            download_thread.start()
            update_buttons("downloading")
            message_label.config(text=_("Downloading..."))

    def on_pause():
        pause_download.set(True)
        update_buttons("paused")
        message_label.config(
            text=_("Download paused. Click Resume to continue."))

    def on_resume():
        pause_download.set(False)
        update_buttons("downloading")
        message_label.config(text=_("Downloading..."))
        if not download_thread or not download_thread.is_alive():
            on_start_download()

    def on_cancel():
        cancel_download.set(True)
        remove_download_state(filename)
        dialog.destroy()

    def update_buttons(state):
        for widget in button_frame.winfo_children():
            widget.destroy()
        if state == "downloading":
            ttk.Button(button_frame, text=_("Pause"), command=on_pause,
                       style='warning.TButton').pack(side="left", padx=10)
            ttk.Button(button_frame, text=_("Cancel"), command=on_cancel,
                       style='danger.TButton').pack(side="left", padx=10)
        elif state == "paused":
            ttk.Button(button_frame, text=_("Resume"), command=on_resume,
                       style='success.TButton').pack(side="left", padx=10)
            ttk.Button(button_frame, text=_("Cancel"), command=on_cancel,
                       style='danger.TButton').pack(side="left", padx=10)
        else:
            ttk.Button(button_frame, text=_("Start Download"), command=on_start_download,
                       style='success.TButton').pack(side="left", padx=10)
            ttk.Button(button_frame, text=_("Cancel"), command=on_cancel,
                       style='danger.TButton').pack(side="left", padx=10)

    def download_and_update_ui(*args):
        result = download_file(*args)
        if result == "completed":
            show_message(self.master, _("Success"),
                         _(f'File downloaded successfully to {os.path.join(download_dir, filename)}'))
            dialog.destroy()
        elif result == "cancelled":
            show_message(self.master, _("Download Cancelled"),
                         _("The download has been cancelled and temporary files removed."))
            dialog.destroy()
        elif result == "failed":
            show_message(self.master, _("Download Failed"),
                         _("The download has failed. You can try to resume it later."))
            update_buttons("paused")
            message_label.config(
                text=_("Download failed. Click Resume to try again."))
        elif result == "paused":
            update_buttons("paused")
            message_label.config(
                text=_("Download paused. Click Resume to continue."))

    download_thread = None
    if download_state:
        total_size = download_state['downloaded_size'] + \
            int(requests.head(download_url).headers.get('content-length', 0))
        update_buttons("paused")
        progress_var.set(
            (download_state['downloaded_size'] / total_size) * 100)
        message_label.config(
            text=_("Previous download found. Click Resume to continue."))
    else:
        update_buttons("initial")

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    dialog.after(10, lambda: center_dialog(dialog, self.master))
    self.master.wait_window(dialog)


def check_for_update(self):
    # GitHub API to get the latest release information
    api_url = f"https://api.github.com/repos/{
        author}/{repo_name}/releases/latest"

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release["tag_name"]

            if is_newer_version(version, latest_version):
                # Get the user's platform (Windows, macOS, Linux)
                user_platform = platform.system()
                arch_platform = platform.version()

                # Extract download link based on platform
                if user_platform == "Windows":
                    download_url = next(asset["browser_download_url"]
                                        for asset in latest_release["assets"] if "windows" in asset["name"].lower())
                elif user_platform == "Darwin" and "arm64" in arch_platform.lower():
                    download_url = next(asset["browser_download_url"]
                                        for asset in latest_release["assets"] if ("mac" in asset["name"].lower() and "arm64" in asset["name"].lower()))
                elif user_platform == "Darwin":
                    download_url = next(asset["browser_download_url"]
                                        for asset in latest_release["assets"] if "mac" in asset["name"].lower() and "arm64" not in asset["name"].lower())
                elif user_platform == "Linux":
                    download_url = next(asset["browser_download_url"]
                                        for asset in latest_release["assets"] if "linux" in asset["name"].lower())
                else:
                    download_url = None

                if download_url:

                    message = _(f'New version {
                                latest_version} is available! Download now ?')
                    ask_download(self, _("Update"), message, download_url)
                else:
                    show_message(self.master, _("Update"), _(
                        "New version is available, but no download is found for your platform."))
            else:
                show_message(self.master, _("No Update Available"),
                             _("You are using the latest version."))
        else:
            show_message(self.master, _("Update Check Failed"), _(
                f'Failed to fetch the latest release info: {response.status_code}'))
    except Exception as e:
        show_message(self.master, _("Error"), _(
            f'An error occurred while checking for updates: {str(e)}'))
