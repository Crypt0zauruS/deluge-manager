#!/bin/bash

# Vérifier si le script est exécuté avec les droits root
if [ "$EUID" -ne 0 ]
  then echo "Ce script doit être exécuté en tant que root. Utilisez sudo."
  exit
fi

# Définir les variables
EXEC_NAME="DelugeManager"
INSTALL_DIR="/usr/local/bin"
ICON_DIR="/usr/share/icons/hicolor"
DESKTOP_FILE="/usr/share/applications/${EXEC_NAME}.desktop"
CONFIG_FILE="$HOME/.config/delugemanager/config.ini"
SCRIPT_NAME=$(basename "$0")
SCRIPT_INSTALL_DIR="/usr/local/lib/delugemanager"
INSTALLED_SCRIPT="$SCRIPT_INSTALL_DIR/$SCRIPT_NAME"

# Fonction pour installer le script
install_script() {
    mkdir -p "$SCRIPT_INSTALL_DIR"
    cp "$0" "$SCRIPT_INSTALL_DIR/$SCRIPT_NAME"
    chmod +x "$SCRIPT_INSTALL_DIR/$SCRIPT_NAME"
    echo "Script d'installation copié dans $SCRIPT_INSTALL_DIR/$SCRIPT_NAME"
}

# Fonction pour vérifier si l'application est déjà installée
check_installation() {
    if [ -f "$INSTALL_DIR/$EXEC_NAME" ]; then
        echo "DelugeManager est déjà installé."
        read -p "Voulez-vous réparer l'installation ? (y/n) " choice
        case "$choice" in 
          y|Y ) echo "Réparation de l'installation..."
                return 0;;
          n|N ) echo "Sortie du script."
                exit 0;;
          * ) echo "Réponse non valide. Sortie du script."
              exit 1;;
        esac
    fi
    return 0
}

# Fonction pour vérifier et installer secret-tool
check_secret_tool() {
    if ! command -v secret-tool &> /dev/null
    then
        echo "Le paquet 'libsecret-tools' n'est pas installé. Il est nécessaire pour gérer les mots de passe du keyring."
        read -p "Voulez-vous l'installer maintenant ? (y/n) " choice
        case "$choice" in 
          y|Y ) apt update && apt install -y libsecret-tools;;
          n|N ) return 1;;
          * ) echo "Réponse non valide. Veuillez répondre par 'y' ou 'n'."
              check_secret_tool;;
        esac
    fi
    return 0
}

# Fonction pour désinstaller
uninstall() {
    echo "Désinstallation de DelugeManager..."

    # Vérifier et installer secret-tool si nécessaire
    if ! check_secret_tool; then
        echo "Impossible de supprimer le mot de passe du keyring sans libsecret-tools."
        read -p "Voulez-vous continuer la désinstallation sans supprimer le mot de passe du keyring ? (y/n) " choice
        case "$choice" in 
          y|Y ) echo "Continuation de la désinstallation sans supprimer le mot de passe du keyring.";;
          n|N ) echo "Désinstallation annulée."
                exit 1;;
          * ) echo "Réponse non valide. Désinstallation annulée."
              exit 1;;
        esac
    else
        # Supprimer le mot de passe du keyring
        secret-tool clear service DelugeApp
    fi

    # Supprimer l'exécutable
    rm -f "$INSTALL_DIR/$EXEC_NAME"

    # Supprimer le fichier .desktop
    rm -f "$DESKTOP_FILE"

    # Supprimer les icônes
    for size in 16 32 48 64 128 256
    do
        rm -f "$ICON_DIR/${size}x${size}/apps/delugemanager.png"
    done

    # Supprimer le fichier de configuration
    rm -f "$CONFIG_FILE"

    echo "Désinstallation terminée."

    # Vérifier si ce script est celui installé dans le système
    if [ "$0" == "$INSTALLED_SCRIPT" ]; then
        # Créer un script temporaire pour supprimer ce script et se supprimer lui-même
        TEMP_SCRIPT=$(mktemp)
        cat << EOF > "$TEMP_SCRIPT"
#!/bin/bash
rm -f "$INSTALLED_SCRIPT"
rmdir --ignore-fail-on-non-empty "$SCRIPT_INSTALL_DIR"
rm -f "$TEMP_SCRIPT"
EOF

        chmod +x "$TEMP_SCRIPT"
        echo "Nettoyage final en cours..."
        "$TEMP_SCRIPT"
    else
        # Si c'est le script original, supprimer directement le script installé
        rm -f "$INSTALLED_SCRIPT"
        rmdir --ignore-fail-on-non-empty "$SCRIPT_INSTALL_DIR"
        echo "Script d'installation système supprimé."
    fi
    
    exit 0
}

# Vérifier si l'option --uninstall est utilisée
if [ "$1" == "--uninstall" ]; then
    uninstall
fi

# Vérifier si l'application est déjà installée
check_installation

# Vérifier la présence des dossiers et fichiers nécessaires
if [ ! -d "./dist" ] || [ ! -f "./dist/DelugeManager" ]; then
    echo "Erreur : Le dossier 'dist' ou l'exécutable 'DelugeManager' est manquant."
    exit 1
fi

if [ ! -d "./linux_icons" ]; then
    echo "Erreur : Le dossier 'linux_icons' est manquant."
    exit 1
fi

# Définir les variables
EXEC_NAME="DelugeManager"
INSTALL_DIR="/usr/local/bin"
ICON_DIR="/usr/share/icons/hicolor"
DESKTOP_FILE="/usr/share/applications/${EXEC_NAME}.desktop"

# Installer l'exécutable
echo "Installation de l'exécutable..."
cp "./dist/$EXEC_NAME" "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/$EXEC_NAME"

# Créer le fichier .desktop
echo "Création du fichier .desktop..."
cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Type=Application
Name=DelugeManager
Comment=Manage your Deluge torrents
Exec=$INSTALL_DIR/$EXEC_NAME
Icon=delugemanager
Categories=Network;FileTransfer;P2P;
EOL

# Installer les icônes
echo "Installation des icônes..."
for size in 16 32 48 64 128 256
do
    icon_path="$ICON_DIR/${size}x${size}/apps"
    mkdir -p "$icon_path"
    cp "linux_icons/icon_${size}x${size}.png" "$icon_path/delugemanager.png"
done

# Mettre à jour la cache des icônes
echo "Mise à jour de la cache des icônes..."
gtk-update-icon-cache -f -t "$ICON_DIR"

# Installer le script
install_script

echo "Installation terminée. Vous pouvez maintenant lancer DelugeManager depuis votre menu d'applications ou en tapant '$EXEC_NAME' dans un terminal."
echo "Pour désinstaller plus tard, exécutez : sudo $SCRIPT_INSTALL_DIR/$SCRIPT_NAME --uninstall"