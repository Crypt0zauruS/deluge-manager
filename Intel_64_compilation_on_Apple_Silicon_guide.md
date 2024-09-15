# Guide de compilation de l'application Python pour Intel Mac sur Mac M1, M2 ou M3

Ce guide détaille le processus de création d'un environnement Conda Intel 64-bit dans le dossier de votre projet sur un Mac Apple Silicon, et la compilation d'une application Python pour l'architecture Intel.

**Note for English-speaking users:**
This tutorial is currently available in French only. An English version is planned for a future update. Thank you for your understanding.

**Note pour les utilisateurs francophones :**
Ce tuto est actuellement disponible uniquement en français. Une version anglaise est prévue pour une mise à jour future.

## Table des matières

1. [Installation de Miniconda](#installation-de-miniconda)
2. [Configuration de l'environnement shell](#configuration-de-lenvironnement-shell)
3. [Création d'un environnement virtuel Conda Intel 64-bit dans le dossier du projet](#création-dun-environnement-conda-intel-64-bit-dans-le-dossier-du-projet)
4. [Installation des dépendances](#installation-des-dépendances)
5. [Compilation de l'application](#compilation-de-lapplication)

## Installation de Miniconda

1. Installez Miniconda en exécutant le script bash téléchargé :

```bash
mkdir -p ~/miniconda3
curl https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh -o ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh
```

2. Initialisez-le dans votre shell bash et/ou zsh :

```bash
~/miniconda3/bin/conda init bash
```

et/ou

```bash
~/miniconda3/bin/conda init zsh
```

3. Désactivez l'activation automatique pour ne pas interférer si vous avez déjà installé python

```bash
~/miniconda3/bin/conda config --set auto_activate_base false
```

## Configuration de l'environnement shell

1. Éditez votre fichier `~/.bash_profile` (pour Bash) et/ou `~/.zshrc` (pour Zsh) et ajoutez les lignes suivantes :

   ```bash
   export PATH="$HOME/miniconda3/bin:$PATH"
   alias activate_conda='eval "$(/Users/votre_nom_d_utilisateur/miniconda3/bin/conda shell.YOUR_SHELL_NAME hook)"'
   ```

   Remplacez votre_nom_d_utilisateur par votre nom d'utilisateur
   Remplacez `YOUR_SHELL_NAME` par `bash` ou `zsh` selon votre shell.

2. Rechargez votre fichier de configuration selon le shell que vous avez initialisé et configuré:

   ```bash
   source ~/.bash_profile
   ```

   et/ou

   ```bash
   source ~/.zshrc
   ```

## Création d'un environnement virtuel Conda Intel 64-bit dans le dossier du projet

1. Naviguez vers le dossier de votre projet :

   ```bash
   cd /chemin/vers/votre/projet
   ```

2. Activez Conda dans le dossier du projet :

   ```bash
   activate_conda
   ```

3. Créez un nouvel environnement Intel 64-bit dans le dossier du projet :

   ```bash
   CONDA_SUBDIR=osx-64 conda create -p ./intel64_env python=3.11
   ```

   Remplacez 3.11 par la version de Python souhaitée

4. Activez l'environnement :

   ```bash
   conda activate ./intel64_env
   ```

5. Configurez l'environnement pour toujours utiliser les packages Intel 64-bit :

   ```bash
   conda config --env --set subdir osx-64
   ```

6. Vérifiez l'architecture :

   ```bash
   python -c "import platform; print(platform.machine())"
   ```

   Cela devrait afficher "x86_64".

## Installation des dépendances

1. Installez toutes les dépendances nécessaires dans l'environnement.

Même si vous avez déjà installé les dépendances précédemment dans l'environnement principal, vous devrez les réinstaller dans l'environnement Intel 64-bit.

Essayez d'abord avec conda (confa-forge est un canal supplémentaire pour ttkbootstrap):

```bash
conda install -y tk requests keyring pyinstaller
conda install -y -c conda-forge ttkbootstrap
```

Si certaines installations échouent avec conda, utilisez pip pour ces packages:

```bash
pip install tk requests keyring pyinstaller ttkbootstrap
```

2. Vérifiez que tout est correctement installé :

```bash
python -c "import tkinter, requests, keyring, ttkbootstrap, PyInstaller; print('Tout est installé correctement!')"
```

## Compilation de l'application

1. Assurez-vous d'être dans le dossier de votre projet et que l'environnement est activé.

2. Compilez l'application :

   ```bash
   pyinstaller --onefile --windowed --icon=icon.icns deluge_manager/main.py --name DelugeManager --osx-bundle-identifier=org.deluge.manager
   ```

3. L'exécutable compilé se trouvera dans le dossier `dist`. Vous aurez également un fichier DelugeManager sans extension, la version pour terminal.

4. Vérifier l'architecture de l'exécutable :

   ```bash
   file dist/DelugeManager
   ```

   Cela devrait afficher "Mach-O 64-bit executable x86_64".

5. Pour quitter l'environnement Conda, exécutez :

   ```bash
   conda deactivate
   ```

6. Si vous n'avez plus besoin de L'environnement virtuel, vous pouvez le supprimer pour nettoyer votre projet :

```bash
conda remove --prefix ./intel64_env --all
rm -rf ./intel64_env
```

## Notes importantes

- Assurez-vous d'être toujours dans l'environnement Conda Intel 64-bit lors de la compilation.
- L'exécutable généré fonctionnera sur les Macs Intel et sur les Macs M1 via Rosetta 2.
- Testez toujours l'application compilée sur différents systèmes pour assurer la compatibilité.
- Si vous déplacez le projet, vous devrez recréer l'environnement car il est spécifique au dossier du projet.
- N'hésitez pas à adapter ces instructions à vos propres projets et besoins !

En suivant ces étapes, vous devriez être en mesure de compiler avec succès votre application Python pour l'architecture Intel, même sur un Mac Apple Silicon, avec l'environnement confiné au dossier de votre projet.
