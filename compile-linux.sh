#!/bin/bash

# Assurez-vous que toutes les dépendances sont installées
pip install -r requirements.txt

# Compiler l'application
pyinstaller --name=DelugeManager \
            --onefile \
            --windowed \
            --add-data "./icon.ico:." \
            --hidden-import ttkbootstrap \
            --hidden-import keyring.backends \
            --hidden-import PIL._tkinter_finder \
            --hidden-import PIL._imaging \
            --collect-all ttkbootstrap \
            --collect-all PIL \
            deluge_manager/main.py

# Vérifier si la compilation a réussi
if [ $? -eq 0 ]; then
    echo "Compilation réussie. L'exécutable se trouve dans le dossier 'dist'."
else
    echo "La compilation a échoué. Vérifiez les erreurs ci-dessus."
fi