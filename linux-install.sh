#!/bin/bash
########################################### French Version ###########################################
# Ce script installe, met à jour, répare ou désinstalle DelugeManager sur Linux.
# Pour désinstaller, exécutez ce script avec l'option --uninstall.
# Pour réparer ou mettre à jour, exécutez ce script à partir du répertoire contenant les fichiers nécessaires.
# L'executable doit être dans un dossier 'dist' et les icônes dans le dossier 'linux_icons'.

########################################### English Version ###########################################
# This script installs, updates, repairs or uninstalls DelugeManager on Linux.
# To uninstall, run this script with the --uninstall option.
# To repair or update, run this script from the directory containing the necessary files.
# The executable should be in a 'dist' folder and the icons in the 'linux_icons' folder.

# Demander la langue à l'utilisateur / Ask the user for the language
echo "Please choose your language: (1) English, (2) Français"
read -p "Enter 1 or 2: " lang_choice

if [ "$lang_choice" == "1" ]; then
    LANGUAGE="en"
elif [ "$lang_choice" == "2" ]; then
    LANGUAGE="fr"
else
    echo "Invalid choice. Defaulting to English."
    LANGUAGE="en"
fi

# Fonction pour afficher les messages
display_message() {
    if [ "$LANGUAGE" == "fr" ]; then
        echo "$1"
    else
        echo "$2"
    fi
}

# Vérifier si le script est exécuté avec les droits root
if [ "$EUID" -ne 0 ]; then
    display_message "Ce script doit être exécuté en tant que root. Utilisez sudo." "This script must be run as root. Use sudo."
    exit 1
fi

# Vérifier et installer ssh-askpass si nécessaire
if ! command -v ssh-askpass &> /dev/null; then
    display_message "ssh-askpass n'est pas installé. Il est utilisé pour automatiser les mises à jour." \
                    "ssh-askpass is not installed. It is used for automating updates."
    read -p "$(display_message 'Voulez-vous installer ssh-askpass maintenant ? (y/n)' 'Do you want to install it now? (y/n)')" choice
    case "$choice" in 
        y|Y ) apt update && apt install -y ssh-askpass;;
        n|N ) display_message "Installation annulée." "Installation cancelled." ; exit 1;;
        * ) display_message "Réponse non valide. Installation annulée." "Invalid response. Installation cancelled." ; exit 1;;
    esac
fi

# Définir les variables
VERSION="0.3.0"
EXEC_NAME="DelugeManager"
INSTALL_DIR="/usr/local/bin"
ICON_DIR="/usr/share/icons/hicolor"
DESKTOP_FILE="/usr/share/applications/${EXEC_NAME}.desktop"
SCRIPT_NAME=$(basename "$0")
SCRIPT_INSTALL_DIR="/usr/local/lib/delugemanager"
INSTALLED_SCRIPT="$SCRIPT_INSTALL_DIR/$SCRIPT_NAME"
VERSION_FILE="$SCRIPT_INSTALL_DIR/version"

# Fonction pour vérifier si les fichiers nécessaires sont présents
base_dir=$(dirname "$(realpath "$0")")

check_necessary_files() {
    if [ ! -d "$base_dir/dist" ] || [ ! -f "$base_dir/dist/DelugeManager" ] || [ ! -d "$base_dir/linux_icons" ]; then
        return 1
    fi
    return 0
}

# Fonction pour installer le script
install_script() {
    mkdir -p "$SCRIPT_INSTALL_DIR"
    cp "$0" "$INSTALLED_SCRIPT"
    chmod +x "$INSTALLED_SCRIPT"
    echo "$VERSION" > "$VERSION_FILE"
    display_message "Script d'installation copié dans $INSTALLED_SCRIPT" "Installation script copied to $INSTALLED_SCRIPT"
}

# Fonction pour désinstaller
uninstall() {
    display_message "Désinstallation de DelugeManager..." "Uninstalling DelugeManager..."

    rm -f "$INSTALL_DIR/$EXEC_NAME"
    rm -f "$DESKTOP_FILE"

    for size in 16 32 48 64 128 256
    do
        rm -f "$ICON_DIR/${size}x${size}/apps/delugemanager.png"
    done

    display_message "Désinstallation terminée." "Uninstallation complete."

    if [ "$0" == "$INSTALLED_SCRIPT" ]; then
        TEMP_SCRIPT=$(mktemp)
        cat << EOF > "$TEMP_SCRIPT"
#!/bin/bash
rm -f "$INSTALLED_SCRIPT"
rm -rf "$SCRIPT_INSTALL_DIR"
rm -f "$TEMP_SCRIPT"
EOF
        chmod +x "$TEMP_SCRIPT"
        display_message "Nettoyage final en cours..." "Final cleanup in progress..."
        "$TEMP_SCRIPT"
    else
        rm -f "$INSTALLED_SCRIPT"
        rm -rf "$SCRIPT_INSTALL_DIR"
        display_message "Script d'installation système supprimé." "Installation script removed."
    fi

    exit 0
}

# Fonction pour installer ou mettre à jour
install_or_update() {
    display_message "Installation/Mise à jour de DelugeManager version $VERSION..." "Installing/Updating DelugeManager version $VERSION..."
    mkdir -p "$INSTALL_DIR"
    cp "$base_dir/dist/$EXEC_NAME" "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/$EXEC_NAME"

    for size in 16 32 48 64 128 256
    do
        icon_path="$ICON_DIR/${size}x${size}/apps"
        mkdir -p "$icon_path"
        cp "$base_dir/linux_icons/icon_${size}x${size}.png" "$icon_path/delugemanager.png"
    done

    cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Type=Application
Name=DelugeManager
Comment=Manage your Deluge torrents
Exec=$INSTALL_DIR/$EXEC_NAME
Icon=delugemanager
Categories=Network;FileTransfer;P2P;
EOL

    gtk-update-icon-cache -f -t "$ICON_DIR"

    install_script

    display_message "Installation/Mise à jour terminée." "Installation/Update complete."
}

# Vérifier les options
case "$1" in
    --uninstall)
        uninstall
        exit 0
        ;;
esac

# Vérifier si les fichiers nécessaires sont présents
if ! check_necessary_files; then
    display_message "Erreur : Les fichiers nécessaires sont manquants. Ce script doit être exécuté à partir du répertoire contenant les dossiers 'dist' et 'linux_icons'." \
                    "Error: Necessary files are missing. This script must be run from the directory containing the 'dist' and 'linux_icons' folders."
    exit 1
fi

# Vérifier si une version est déjà installée
if [ -f "$VERSION_FILE" ]; then
    INSTALLED_VERSION=$(cat "$VERSION_FILE")
    if [ "$INSTALLED_VERSION" = "$VERSION" ]; then
        display_message "La version $VERSION est déjà installée. Voulez-vous réparer l'installation ? (y/n)" \
                        "Version $VERSION is already installed. Do you want to repair the installation? (y/n)"
        read choice
        case "$choice" in
            y|Y )
                display_message "Réparation de l'installation..." "Repairing installation..."
                uninstall
                install_or_update
                ;;
            * )
                display_message "Opération annulée." "Operation cancelled."
                exit 0
                ;;
        esac
    elif [ "$INSTALLED_VERSION" \< "$VERSION" ]; then
        display_message "Une mise à jour est disponible (version installée : $INSTALLED_VERSION, nouvelle version : $VERSION). Voulez-vous mettre à jour ? (y/n)" \
                        "An update is available (installed version: $INSTALLED_VERSION, new version: $VERSION). Do you want to update? (y/n)"
        read choice
        case "$choice" in
            y|Y )
                display_message "Mise à jour en cours..." "Updating..."
                uninstall
                install_or_update
                ;;
            * )
                display_message "Mise à jour annulée." "Update cancelled."
                exit 0
                ;;
        esac
    else
        display_message "La version installée ($INSTALLED_VERSION) est plus récente que la version à installer ($VERSION). Installation annulée." \
                        "The installed version ($INSTALLED_VERSION) is newer than the version to install ($VERSION). Installation cancelled."
        exit 1
    fi
else
    display_message "Nouvelle installation en cours..." "New installation in progress..."
    install_or_update
fi

display_message "Vous pouvez maintenant lancer DelugeManager depuis votre menu d'applications ou en tapant '$EXEC_NAME' dans un terminal." \
                "You can now launch DelugeManager from your applications menu or by typing '$EXEC_NAME' in a terminal."
display_message "Pour désinstaller plus tard, exécutez : sudo $INSTALLED_SCRIPT --uninstall" \
                "To uninstall later, run: sudo $INSTALLED_SCRIPT --uninstall"
