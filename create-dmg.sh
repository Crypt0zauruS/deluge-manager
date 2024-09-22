#!/bin/bash

# Assurez-vous que create-dmg et ImageMagick sont installés
# installer Homebrew (https://brew.sh/) si ce n'est pas déjà fait
# brew install create-dmg imagemagick

# Définissez vos variables / Define your variables
APP_NAME="DelugeManager"
DMG_NAME="${APP_NAME}.dmg"
APP_PATH="./dist/${APP_NAME}.app"
ORIGINAL_BACKGROUND="./docs/DM.png"
TEXT_COLOR="1.0 1.0 1.0"

# Définissez la taille de la fenêtre DMG / Set the DMG window size
WINDOW_WIDTH=800
WINDOW_HEIGHT=450

# Créez un dossier temporaire pour les fichiers de travail / Create a temporary directory for working files
TEMP_DIR=$(mktemp -d)
BACKGROUND_IMG="${TEMP_DIR}/background.png"

# Redimensionnez l'image de fond pour qu'elle remplisse la fenêtre tout en préservant son ratio
# Resize the background image to fill the window while preserving its aspect ratio
magick "${ORIGINAL_BACKGROUND}" -resize "${WINDOW_WIDTH}x${WINDOW_HEIGHT}^" -gravity center -extent ${WINDOW_WIDTH}x${WINDOW_HEIGHT} "${BACKGROUND_IMG}"

# Créez le DMG / Create the DMG
create-dmg \
  --volname "${APP_NAME}" \
  --volicon "./icon.icns" \
  --background "${BACKGROUND_IMG}" \
  --window-pos 200 120 \
  --window-size ${WINDOW_WIDTH} ${WINDOW_HEIGHT} \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 200 190 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 600 185 \
  "${DMG_NAME}" \
  "${APP_PATH}"

# Nettoyage / Clean up
rm -rf "${TEMP_DIR}"

echo "DMG créé avec succès : ${DMG_NAME}"