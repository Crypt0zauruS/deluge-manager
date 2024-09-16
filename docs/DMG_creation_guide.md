# Création du DMG pour DelugeManager

Ce document explique comment créer un fichier DMG (Disk Image) personnalisé pour l'application DelugeManager sur macOS.
La procédure est la même quelque soit l'architecture (Intel ou Apple Silicon).

**Note for English-speaking users:**
This tutorial is currently available in French only. An English version is planned for a future update. Thank you for your understanding.

**Note pour les utilisateurs francophones :**
Ce tuto est actuellement disponible uniquement en français. Une version anglaise est prévue pour une mise à jour future.

## Prérequis

Avant de commencer, assurez-vous d'avoir installé :

1. **Homebrew** : Un gestionnaire de paquets pour macOS. Si vous ne l'avez pas, installez-le depuis [https://brew.sh/](https://brew.sh/)

2. **create-dmg** : Un outil pour créer des DMG personnalisés

   ```
   brew install create-dmg
   ```

3. **ImageMagick** : Un outil de manipulation d'images
   ```
   brew install imagemagick
   ```

## Fichiers nécessaires

Assurez-vous d'avoir les fichiers suivants dans votre répertoire de travail :

- `DelugeManager.app` : Votre application compilée dans le répertoire `/dist`
- `icon.icns` : L'icône de votre application
- `DM.png` : L'image de fond pour le DMG

## Le script de création du DMG

Le script `create-dmg.sh` automatise le processus de création du DMG. Voici ses principales fonctionnalités :

1. Redimensionne l'image de fond pour s'adapter à la taille de la fenêtre du DMG
2. Crée un DMG avec une disposition personnalisée
3. Configure l'apparence du DMG (taille de la fenêtre, position des icônes, etc.)
4. Le script assume que DelugeManager.app compilée est dans /dist, et icon.icns, DM.png sont présents dans le répertoire racine.

## Utilisation du script

1. Ouvrez un terminal et naviguez vers le répertoire du projet.

2. Rendez le script exécutable :

   ```
   chmod +x create-dmg.sh
   ```

3. Exécutez le script :

   ```
   ./create-dmg.sh
   ```

   Attendez que "DMG créé avec succès" s'affiche dans le terminal (vous verrez l'interface du dmg apparaitre à l'écran et changer durant sa construction, mais ne touchez à rien).

4. Une fois terminé, vous trouverez le fichier `DelugeManager.dmg` dans le même répertoire.

## Personnalisation

Vous pouvez personnaliser plusieurs aspects du DMG en modifiant les variables dans le script :

- `APP_NAME` : Le nom de votre application
- `WINDOW_WIDTH` et `WINDOW_HEIGHT` : La taille de la fenêtre du DMG
- `TEXT_COLOR` : La couleur du texte des icônes (format RGB, valeurs entre 0.0 et 1.0)

Vous pouvez également ajuster la position des icônes en modifiant les coordonnées dans les options de `create-dmg`.

## Dépannage

Si vous rencontrez des problèmes :

1. Assurez-vous que tous les prérequis sont correctement installés.
2. Vérifiez que tous les fichiers nécessaires sont présents dans le répertoire de travail.
3. Assurez-vous que les chemins dans le script sont corrects pour votre configuration.

## Notes supplémentaires

- Le script crée un dossier temporaire pour traiter l'image de fond. Ce dossier est automatiquement supprimé à la fin du processus.
- L'image de fond est redimensionnée pour remplir complètement la fenêtre du DMG tout en préservant son ratio d'aspect.
- Vous pouvez modifier l'image de fond en remplaçant `DM.png` par une autre image de votre choix.
