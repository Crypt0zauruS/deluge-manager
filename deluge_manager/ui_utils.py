import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import webbrowser
import sys
import platform
from localization import _
from datetime import datetime

author = "Crypt0zauruS"
version = "0.3.0"
repo_name = "deluge-manager"
repo = f"https://github.com/{author}/{repo_name}"
issues = f"https://github.com/{author}/{repo_name}/issues"


def format_size(size_in_bytes):
    for unit in [_('B'), _('KB'), _('MB'), _('GB')]:
        if size_in_bytes < 1024.0:
            return _("{:.2f} {}").format(size_in_bytes, unit)
        size_in_bytes /= 1024.0
    return _("{:.2f} TB").format(size_in_bytes)


def format_speed(speed_in_bytes):
    speed_in_kb = speed_in_bytes / 1024
    if speed_in_kb < 1024:
        return _("{:.2f} KB/s").format(speed_in_kb)
    else:
        return _("{:.2f} MB/s").format(speed_in_kb/1024)


def format_eta(eta_in_seconds):
    if eta_in_seconds == 0:
        return _("Finished")
    elif eta_in_seconds < 0:
        return _("Unknown")
    else:
        hours, remainder = divmod(eta_in_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return _("{}h {}m").format(int(hours), int(minutes))


def show_message(master, title, message, message_type="info"):
    dialog = tk.Toplevel(master)
    dialog.title(_(title))
    dialog.geometry("400x250")
    dialog.minsize(400, 250)
    dialog.resizable(True, True)

    dialog.transient(master)
    dialog.grab_set()

    frame = ttk.Frame(dialog, padding="20 20 20 20")
    frame.pack(fill=tk.BOTH, expand=True)

    icons = {
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️"
    }
    icon_label = ttk.Label(frame, text=icons.get(
        message_type, "ℹ️"), font=("TkDefaultFont", 48))
    icon_label.pack(pady=(0, 10))

    max_length = 150
    truncated_message = message[:max_length]
    if len(message) > max_length:
        truncated_message += "..."

    message_label = ttk.Label(
        frame, text=truncated_message, wraplength=360, justify="center")
    message_label.pack(expand=True)

    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=10, fill=tk.X)

    def close_dialog():
        dialog.grab_release()
        dialog.destroy()

    def copy_full_message():
        dialog.clipboard_clear()
        dialog.clipboard_append(message)
        dialog.update()

    ttk.Button(button_frame, text=_("OK"), command=close_dialog,
               style='primary.TButton').pack(side=tk.LEFT, expand=True, padx=(0, 5))

    if len(message) > max_length:
        ttk.Button(button_frame, text=_("Copy full message"), command=copy_full_message,
                   style='info.TButton').pack(side=tk.LEFT, expand=True, padx=(5, 0))

    dialog.after(10, lambda: center_dialog(dialog, master))
    master.wait_window(dialog)


def ask_yes_no(master, title, message):
    dialog = tk.Toplevel(master)
    dialog.title(_(title))
    dialog.geometry("400x250")
    dialog.minsize(400, 250)
    dialog.resizable(True, True)

    dialog.transient(master)
    dialog.grab_set()

    frame = ttk.Frame(dialog, padding="20 20 20 20")
    frame.pack(fill=tk.BOTH, expand=True)

    icon_label = ttk.Label(frame, text="❓", font=("TkDefaultFont", 48))
    icon_label.pack(pady=(0, 10))

    ttk.Label(frame, text=message, wraplength=360,
              justify="center").pack(expand=True)

    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=10)

    result = tk.BooleanVar(value=False)

    def on_yes():
        result.set(True)
        dialog.destroy()

    def on_no():
        result.set(False)
        dialog.destroy()

    ttk.Button(button_frame, text=_("Yes"), command=on_yes,
               style='success.TButton').pack(side="left", padx=10)
    ttk.Button(button_frame, text=_("No"), command=on_no,
               style='danger.TButton').pack(side="left", padx=10)

    dialog.after(10, lambda: center_dialog(dialog, master))

    master.wait_window(dialog)

    return result.get()


def show_about(master):
    about_window = tk.Toplevel(master)
    about_window.title(_("About DelugeManager"))
    about_window.geometry("400x350")
    about_window.resizable(False, False)

    style = ttk.Style()
    style.configure("TNotebook.Tab", padding=(10, 5))

    notebook = ttk.Notebook(about_window)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    # Onglet Général
    general_frame = ttk.Frame(notebook)
    notebook.add(general_frame, text=_("General"))

    def current_year():
        return datetime.now().year
    ttk.Label(general_frame, text="DelugeManager", font=(
        "TkDefaultFont", 16, "bold")).pack(pady=10)
    ttk.Label(general_frame, text=f"Version {version}").pack()
    ttk.Label(general_frame, text=f"© {current_year()} {author}").pack()

    ttk.Label(general_frame, text=_("All rights reserved")).pack(pady=(0, 10))

    ttk.Button(general_frame, text=_("Visit GitHub"),
               command=lambda: webbrowser.open(repo)).pack(pady=5)
    ttk.Button(general_frame, text=_("Report an issue"),
               command=lambda: webbrowser.open(issues)).pack(pady=5)

    # Onglet Système
    system_frame = ttk.Frame(notebook)
    notebook.add(system_frame, text=_("System Info"))

    system_info = _("OS: {}\n\n{}\n\n").format(
        platform.system(), platform.version())
    system_info += _("Python: {}\n\n").format(sys.version.split()[0])
    system_info += _("Tkinter: {}").format(tk.TkVersion)

    ttk.Label(system_frame, text=_("System Information"),
              font=("TkDefaultFont", 12, "bold")).pack(pady=10)

    info_text = tk.Text(system_frame, wrap=tk.WORD, height=8, width=40)
    info_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
    info_text.insert(tk.END, system_info)
    info_text.config(state=tk.DISABLED)  # Rend le texte en lecture seule

    # Ajout d'une scrollbar si nécessaire
    '''
    scrollbar = ttk.Scrollbar(
        system_frame, orient="vertical", command=info_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    info_text.configure(yscrollcommand=scrollbar.set)
    '''

    # Onglet Licence
    license_frame = ttk.Frame(notebook)
    notebook.add(license_frame, text=_("License"))

    license_text = _(
        "This project is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).\n\n")
    license_text += _("You are free to:\n")
    license_text += _("- Share: copy and redistribute the material in any medium or format\n")
    license_text += _("- Adapt: remix, transform, and build upon the material\n\n")
    license_text += _("Under the following terms:\n")
    license_text += _("- Attribution: You must give appropriate credit, provide a link to the license, and indicate if changes were made.")

    license_textbox = tk.Text(license_frame, wrap=tk.WORD, height=10)
    license_textbox.pack(padx=10, pady=10, fill="both", expand=True)
    license_textbox.insert("1.0", license_text)
    license_textbox.config(state="disabled")

    ttk.Button(about_window, text=_("Close"),
               command=about_window.destroy).pack(pady=10)

    center_dialog(about_window, master)

    about_window.transient(master)
    about_window.grab_set()
    master.wait_window(about_window)


def center_dialog(dialog, master):
    dialog.update_idletasks()
    main_width = master.winfo_width()
    main_height = master.winfo_height()
    main_x = master.winfo_rootx()
    main_y = master.winfo_rooty()
    dialog_width = dialog.winfo_width()
    dialog_height = dialog.winfo_height()
    x = main_x + (main_width - dialog_width) // 2
    y = main_y + (main_height - dialog_height) // 2
    dialog.geometry(f"+{x}+{y}")


def update_button_state(self):
    if self.is_connected:
        self.connect_button.pack_forget()
        self.disconnect_button.pack(side=tk.LEFT, padx=5)
        self.edit_tracker_button.pack(side=tk.LEFT, padx=5)
        self.update_credentials_button.pack_forget()
        self.clear_credentials_button.pack_forget()
    else:
        self.disconnect_button.pack_forget()
        self.edit_tracker_button.pack_forget()
        self.connect_button.pack(side=tk.LEFT, padx=5)
        self.update_credentials_button.pack(side=tk.LEFT, padx=5)
        self.clear_credentials_button.pack(side=tk.LEFT, padx=5)


def create_entry_with_paste(self, parent, textvariable, show=None):
    frame = ttk.Frame(parent)
    entry = ttk.Entry(frame, textvariable=textvariable, show=show, width=40)
    entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

    def safe_paste():
        try:
            clipboard_content = self.master.clipboard_get()
            textvariable.set(clipboard_content)
        except tk.TclError:
            print("No clipboard content to paste.")

    paste_button = ttk.Button(frame, text="📋",
                              command=safe_paste,
                              style='info.Outline.TButton', width=3)
    paste_button.pack(side=tk.RIGHT, padx=(5, 0))

    return frame


def create_menus(self):
    self.menu_bar.delete(0, tk.END)

    help_menu = tk.Menu(self.menu_bar, tearoff=0)
    self.menu_bar.add_cascade(label=_("Help"), menu=help_menu)
    help_menu.add_command(
        label=_("About"), command=lambda: show_about(self.master))

    settings_menu = tk.Menu(self.menu_bar, tearoff=0)
    self.menu_bar.add_cascade(label=_("Settings"), menu=settings_menu)
    settings_menu.add_command(
        label=_("Preferences"), command=self.open_settings)

    language_menu = tk.Menu(settings_menu, tearoff=0)
    settings_menu.add_cascade(label=_("Language"), menu=language_menu)
    language_menu.add_command(
        label=_("French"), command=lambda: self.change_app_language('fr'))
    language_menu.add_command(
        label=_("English"), command=lambda: self.change_app_language('en'))


def configure_button_style(self, style):
    style.configure("Purple.TButton",
                    background="#8E44AD",
                    foreground="white",
                    borderwidth=0,
                    focuscolor="#8E44AD",
                    lightcolor="#8E44AD",
                    darkcolor="#8E44AD",
                    relief="flat",
                    padding=(10, 5))

    style.map("Purple.TButton",
              background=[('active', '#9B59B6'), ('pressed', '#7D3C98')],
              foreground=[('active', 'white'), ('pressed', 'white')],
              bordercolor=[('active', '#9B59B6'), ('pressed', '#7D3C98')],
              lightcolor=[('active', '#9B59B6'), ('pressed', '#7D3C98')],
              darkcolor=[('active', '#9B59B6'), ('pressed', '#7D3C98')])


def configure_treeview(self):
    self.tree.tag_configure('oddrow', background='#2a3038')
    self.tree.tag_configure('evenrow', background='#212529')
    self.tree.tag_configure('downloading', background='#D3D3D3')
    self.tree.tag_configure(
        'error', background='orangered', foreground='black')

    for col, header in zip(['name', 'size', 'progress', 'down_speed', 'up_speed', 'eta', 'state'],
                           [_("Name"), _("Size"), _("Progress"), _("Down Speed"), _("Up Speed"), _("ETA"), _("State")]):
        self.tree.heading(col, text=header)
        self.tree.column(col, width=100, anchor='center')

    self.tree.column('name', width=300, anchor='w')
    style = ttk.Style()
    style.configure("Treeview", background='systemTransparent',
                    fieldbackground='systemTransparent', foreground='white')
    style.configure("Treeview.Heading",
                    background='darkgrey', foreground='black')


def update_button_texts(self):
    self.connect_button.config(text=_("Connection"))
    self.disconnect_button.config(text=_("Disconnect"))
    self.update_credentials_button.config(text=_("Update Credentials"))
    self.clear_credentials_button.config(text=_("Clear Credentials"))
    self.load_torrent_button.config(text=_("Load Torrent(s)"))
    self.add_magnet_button.config(text=_("Send Magnet"))


def update_label_texts(self):
    self.delete_torrent_checkbox.config(
        text=_("Delete .torrent after loading"))
