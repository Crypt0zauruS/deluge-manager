import tkinter as tk
import ttkbootstrap as ttk


def format_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"


def format_speed(speed_in_bytes):
    speed_in_kb = speed_in_bytes / 1024
    if speed_in_kb < 1024:
        return f"{speed_in_kb:.2f} KB/s"
    else:
        return f"{speed_in_kb/1024:.2f} MB/s"


def format_eta(eta_in_seconds):
    if eta_in_seconds == 0:
        return "Terminé"
    elif eta_in_seconds < 0:
        return "Inconnu"
    else:
        hours, remainder = divmod(eta_in_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m"


def show_message(master, title, message, message_type="info"):
    dialog = tk.Toplevel(master)
    dialog.title(title)
    dialog.geometry("400x250")
    dialog.minsize(400, 250)
    dialog.resizable(True, True)

    dialog.transient(master)
    dialog.grab_set()

    frame = ttk.Frame(dialog, padding="20 20 20 20")
    frame.pack(fill=tk.BOTH, expand=True)

    # Icônes pour différents types de messages
    icons = {
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️"
    }
    icon_label = ttk.Label(frame, text=icons.get(
        message_type, "ℹ️"), font=("TkDefaultFont", 48))
    icon_label.pack(pady=(0, 10))

    # Tronquer le message si nécessaire
    max_length = 150  # Nombre maximal de caractères à afficher
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
        dialog.update()  # Nécessaire pour que le presse-papiers soit mis à jour immédiatement

    ttk.Button(button_frame, text="OK", command=close_dialog,
               style='primary.TButton').pack(side=tk.LEFT, expand=True, padx=(0, 5))

    if len(message) > max_length:
        ttk.Button(button_frame, text="Copier le message complet", command=copy_full_message,
                   style='info.TButton').pack(side=tk.LEFT, expand=True, padx=(5, 0))

    dialog.after(10, lambda: center_dialog(dialog, master))
    master.wait_window(dialog)


def ask_yes_no(master, title, message):
    dialog = tk.Toplevel(master)
    dialog.title(title)
    dialog.geometry("400x250")
    dialog.minsize(400, 250)
    dialog.resizable(True, True)

    # Rendre la fenêtre modale
    dialog.transient(master)
    dialog.grab_set()

    frame = ttk.Frame(dialog, padding="20 20 20 20")
    frame.pack(fill=tk.BOTH, expand=True)

    # Icône pour la question
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

    ttk.Button(button_frame, text="Oui", command=on_yes,
               style='success.TButton').pack(side="left", padx=10)
    ttk.Button(button_frame, text="Non", command=on_no,
               style='danger.TButton').pack(side="left", padx=10)

    # Centrer la boîte de dialogue
    dialog.after(10, lambda: center_dialog(dialog, master))

    # Attendre que la fenêtre soit fermée
    master.wait_window(dialog)

    return result.get()


def center_dialog(dialog, master):
    """
    Centre une boîte de dialogue par rapport à sa fenêtre maître.

    :param dialog: La boîte de dialogue à centrer (tk.Toplevel)
    :param master: La fenêtre maître (tk.Tk ou tk.Toplevel)
    """
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
