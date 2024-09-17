#!/bin/bash

# Vérifier si le script est exécuté avec les droits root
if [ "$EUID" -ne 0 ]
  then echo "Ce script doit être exécuté en tant que root. Utilisez sudo."
  exit
fi

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

echo "Installation terminée. Vous pouvez maintenant lancer DelugeManager depuis votre menu d'applications ou en tapant '$EXEC_NAME' dans un terminal."