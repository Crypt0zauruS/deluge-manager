import tkinter as tk
import ttkbootstrap as ttk
import tkinter.colorchooser as colorchooser
from ui_utils import center_dialog, show_message
from localization import _


class ColorPickerButton(ttk.Button):
    def __init__(self, master, initial_color, **kwargs):
        super().__init__(master, **kwargs)
        self.color = initial_color
        self.configure(command=self.pick_color)
        self.update_color()

    def pick_color(self):
        parent_window = self.winfo_toplevel()
        color = colorchooser.askcolor(
            color=self.color,
            parent=parent_window,
            title=_("Choose a color"),
            initialcolor=self.color
        )

        if color[1]:
            self.color = color[1]
            self.update_color()
            self.master.focus_set()

    def update_color(self):
        self.configure(style='ColorButton.TButton')
        style = ttk.Style()
        style.configure('ColorButton.TButton', background=self.color)
        self.configure(text=_("Choose a color"))


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, initial_color, initial_size):
        super().__init__(parent)
        self.title(_("Settings"))
        self.geometry("500x250")
        self.resizable(False, False)
        self.result = None

        frame = ttk.Frame(self, padding=(20, 20, 20, 20))
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=_("Downloading torrent color:")).grid(
            row=0, column=0, sticky='w', pady=10)
        self.color_button = ColorPickerButton(
            frame, initial_color, text=_("Choose a color"))
        self.color_button.grid(row=0, column=1, sticky='ew', pady=10)

        ttk.Label(frame, text=_("Window dimensions:")).grid(
            row=1, column=0, sticky='w', pady=10)
        size_frame = ttk.Frame(frame)
        size_frame.grid(row=1, column=1, sticky='ew', pady=10)

        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()

        self.width_entry = ttk.Entry(
            size_frame, width=6, textvariable=self.width_var)
        self.width_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(size_frame, text="x").pack(side=tk.LEFT, padx=5)
        self.height_entry = ttk.Entry(
            size_frame, width=6, textvariable=self.height_var)
        self.height_entry.pack(side=tk.LEFT, padx=(5, 0))

        width, height = initial_size.split('x')
        self.width_var.set(width)
        self.height_var.set(height)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text=_("Apply"),
                   command=self.apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text=_("Cancel"),
                   command=self.cancel).pack(side=tk.LEFT, padx=5)

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        center_dialog(self, parent)

    def apply(self):
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())

            if width < 1200 or height < 800:
                show_message(self, _("Error"), _(
                    "Minimum dimensions are 1200x800. Please enter valid values."))
                return

            self.result = (self.color_button.color, f"{width}x{height}")
            self.destroy()
        except ValueError:
            show_message(self, _("Error"), _(
                "Please enter valid numbers for width and height."))

    def cancel(self):
        self.result = None
        self.destroy()


def open_settings_dialog(master, config, config_file):
    current_color = config.get(
        'Settings', 'download_color', fallback='#D3D3D3')
    current_size = config.get('Settings', 'window_size', fallback='1200x900')

    dialog = SettingsDialog(master, current_color, current_size)
    center_dialog(dialog, master)
    master.wait_window(dialog)

    if dialog.result:
        new_color, new_size = dialog.result
        config['Settings']['download_color'] = new_color
        config['Settings']['window_size'] = new_size
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        return True
    return False


def load_settings(config, master, tree):
    download_color = config.get(
        'Settings', 'download_color', fallback='#D3D3D3')
    window_size = config.get('Settings', 'window_size', fallback='1200x900')
    master.geometry(window_size)
    tree.tag_configure('downloading', background=download_color)


def get_color_for_progress(progress, base_color):
    # Couleur de départ (gris clair)
    # Valeurs RGB pour #D3D3D3 (gris clair)
    start_r, start_g, start_b = 211, 211, 211

    # Couleur cible (couleur définie dans le fichier ini)
    target_r, target_g, target_b = int(base_color[1:3], 16), int(
        base_color[3:5], 16), int(base_color[5:7], 16)

    # Calcul de la couleur intermédiaire
    r = int(start_r + (target_r - start_r) * (progress / 100))
    g = int(start_g + (target_g - start_g) * (progress / 100))
    b = int(start_b + (target_b - start_b) * (progress / 100))

    # Assurer que les valeurs sont dans la plage 0-255
    r = max(0, min(r, 255))
    g = max(0, min(g, 255))
    b = max(0, min(b, 255))

    return f'#{r:02x}{g:02x}{b:02x}'
