<details>
<style>
summary {
  font-size: 2em;
  font-weight: bold;
  margin-bottom: 10px;
  cursor: pointer;
}
</style>
<summary>English (Click to expand)</summary>

# Guide to Compiling Python Application for Intel Mac on M1, M2, or M3 Mac

This guide details the process of creating an Intel 64-bit Conda environment in your project folder on an Apple Silicon Mac, and compiling a Python application for the Intel architecture.

## Table of Contents

1. [Installing Miniconda](#installing-miniconda)
2. [Configuring the Shell Environment](#configuring-the-shell-environment)
3. [Creating an Intel 64-bit Conda Environment in the Project Folder](#creating-an-intel-64-bit-conda-environment-in-the-project-folder)
4. [Installing Dependencies](#installing-dependencies)
5. [Compiling the Application](#compiling-the-application)

## Installing Miniconda

1. Install Miniconda by running the downloaded bash script:

```bash
mkdir -p ~/miniconda3
curl https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh -o ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh
```

2. Initialize it in your bash and/or zsh shell:

```bash
~/miniconda3/bin/conda init bash
```

and/or

```bash
~/miniconda3/bin/conda init zsh
```

3. Disable automatic activation to avoid interference if you have already installed Python:

```bash
~/miniconda3/bin/conda config --set auto_activate_base false
```

## Configuring the Shell Environment

1. Edit your `~/.bash_profile` (for Bash) and/or `~/.zshrc` (for Zsh) file and add the following lines:

   ```bash
   export PATH="$HOME/miniconda3/bin:$PATH"
   alias activate_conda='eval "$(/Users/your_username/miniconda3/bin/conda shell.YOUR_SHELL_NAME hook)"'
   ```

   Replace `your_username` with your actual username.
   Replace `YOUR_SHELL_NAME` with `bash` or `zsh` depending on your shell.

2. Reload your configuration file according to the shell you initialized and configured:

   ```bash
   source ~/.bash_profile
   ```

   and/or

   ```bash
   source ~/.zshrc
   ```

## Creating an Intel 64-bit Conda Environment in the Project Folder

1. Navigate to your project folder:

   ```bash
   cd /path/to/your/project
   ```

2. Activate Conda in the project folder:

   ```bash
   activate_conda
   ```

3. Create a new Intel 64-bit environment in the project folder:

   ```bash
   CONDA_SUBDIR=osx-64 conda create -p ./intel64_env python=3.12
   ```

   Replace 3.12 with your desired Python version.

4. Activate the environment:

   ```bash
   conda activate ./intel64_env
   ```

5. Configure the environment to always use Intel 64-bit packages:

   ```bash
   conda config --env --set subdir osx-64
   ```

6. Verify the architecture:

   ```bash
   python -c "import platform; print(platform.machine())"
   ```

   This should display "x86_64".

## Installing Dependencies

1. Install all necessary dependencies in the environment.

Even if you have previously installed dependencies in the main environment, you will need to reinstall them in the Intel 64-bit environment.

```bash
conda install -y tk requests keyring pyinstaller Pillow
```

Install ttkbootstrap and pyinstaller via pip:

```bash
pip install ttkbootstrap
```

2. Verify that everything is correctly installed:

```bash
python -c "import tkinter, requests, keyring, ttkbootstrap, PyInstaller; print('Everything is installed correctly!')"
```

## Compiling the Application

1. Make sure you are in your project folder and the environment is activated.

2. Compile the application:

   ```bash
   pyinstaller DelugeManager.spec
   ```

3. The compiled executable will be in the `dist` folder. You will also have a DelugeManager file without extension, which is the terminal version.

4. Verify the architecture of the executable:

   ```bash
   file dist/DelugeManager
   ```

   This should display "Mach-O 64-bit executable x86_64".

5. To exit the Conda environment, run:

   ```bash
   conda deactivate
   ```

6. If you no longer need the virtual environment, you can remove it to clean up your project:

```bash
conda env remove --name intel64_env
rm -rf ./intel64_env
```

## Important Notes

- Make sure you are always in the Intel 64-bit Conda environment when compiling.
- The generated executable will work on Intel Macs and on M1 Macs via Rosetta 2.
- Always test the compiled application on different systems to ensure compatibility.
- If you move the project, you'll need to recreate the environment as it's specific to the project folder.
- You can create the DMG with the provided script even in your usual environment (no need for the Intel 64-bit environment).
- Feel free to adapt these instructions to your own projects and needs!

By following these steps, you should be able to successfully compile your Python application for the Intel architecture, even on an Apple Silicon Mac, with the environment confined to your project folder.

</details>

<details>

<summary>Français (Cliquez pour déplier)</summary>

# Guide de compilation de l'application Python pour Intel Mac sur Mac M1, M2 ou M3

Ce guide détaille le processus de création d'un environnement Conda Intel 64-bit dans le dossier de votre projet sur un Mac Apple Silicon, et la compilation d'une application Python pour l'architecture Intel.

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
   CONDA_SUBDIR=osx-64 conda create -p ./intel64_env python=3.12
   ```

   Remplacez 3.12 par la version de Python souhaitée

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

```bash
conda install -y tk requests keyring pyinstaller Pillow
```

Installez ttkbootstrap et pyinstaller via pip :

```bash
pip install ttkbootstrap
```

2. Vérifiez que tout est correctement installé :

```bash
python -c "import tkinter, requests, keyring, ttkbootstrap, PyInstaller; print('Tout est installé correctement!')"
```

## Compilation de l'application

1. Assurez-vous d'être dans le dossier de votre projet et que l'environnement est activé.

2. Compilez l'application :

   ```bash
   pyinstaller DelugeManager.spec
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
conda env remove --name intel64_env
rm -rf ./intel64_env
```

## Notes importantes

- Assurez-vous d'être toujours dans l'environnement Conda Intel 64-bit lors de la compilation.
- L'exécutable généré fonctionnera sur les Macs Intel et sur les Macs M1 via Rosetta 2.
- Testez toujours l'application compilée sur différents systèmes pour assurer la compatibilité.
- Si vous déplacez le projet, vous devrez recréer l'environnement car il est spécifique au dossier du projet.
- vous pouvez créer le DMG avec le script fourni même dans votre environnement habituel (pas besoin de l'environnement Intel 64-bit)
- N'hésitez pas à adapter ces instructions à vos propres projets et besoins !

En suivant ces étapes, vous devriez être en mesure de compiler avec succès votre application Python pour l'architecture Intel, même sur un Mac Apple Silicon, avec l'environnement confiné au dossier de votre projet.

</details>
