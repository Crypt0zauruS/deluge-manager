# -*- mode: python ; coding: utf-8 -*-

import sys
import platform
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# read requirements.txt
with open('requirements.txt', 'r') as req_file:
    requirements = [line.strip() for line in req_file if line.strip() and not line.startswith('#')]

# Collecter toutes les dépendances
all_datas = []
all_binaries = []
all_hiddenimports = []

for requirement in requirements:
    datas, binaries, hiddenimports = collect_all(requirement.split('==')[0])
    all_datas.extend(datas)
    all_binaries.extend(binaries)
    all_hiddenimports.extend(hiddenimports)

# Add local modules
local_modules = ['torrents_actions', 'torrents_loader', 
                 'torrents_updater', 'ui_utils']
all_hiddenimports.extend(local_modules)

# Add local data
all_datas.extend([('deluge_manager/*.py', '.'),  
                  ('deluge_manager/banner.png', '.')])

a = Analysis(['deluge_manager/main.py'],  
             pathex=['.', './deluge_manager'],  # Pathex adds the current directory to the path
             binaries=all_binaries,
             datas=all_datas,
             hiddenimports=all_hiddenimports + ['ttkbootstrap', 'keyring.backends', 
                                                'PIL._tkinter_finder', 'PIL._imaging'] 
                          + collect_submodules('keyring.backends'),
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

# Definition of icons for the different platforms
if sys.platform == 'darwin':
    icon = 'icon.icns'
elif sys.platform.startswith('win'):
    icon = 'icon.ico'
else:
    icon = None

# Definition of version information for the Windows executable
version_info = {
    'version': '0.2.0',
    'company_name': 'Crypt0zauruS',
    'file_description': 'DelugeManager - A Deluge Torrent Client Manager',
    'internal_name': 'DelugeManager',
    'legal_copyright': 'Copyright © 2024 Crypt0zauruS. All rights reserved.',
    'original_filename': 'DelugeManager.exe',
    'product_name': 'DelugeManager',
}

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='DelugeManager',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon=icon,
          version_info=version_info if sys.platform.startswith('win') else None,
          )

# Definition of the final application for macOS
if sys.platform == 'darwin':
    app = BUNDLE(exe,
                 name='DelugeManager.app',
                 icon=icon,
                 bundle_identifier='org.deluge.manager',
                 version='0.2.0',
                 info_plist={
                     'NSHumanReadableCopyright': 'Copyright © 2024 Crypt0zauruS. All rights reserved.',
                     'CFBundleShortVersionString': '0.2.0',
                     'CFBundleVersion': '0.2.0',
                     'NSHighResolutionCapable': True,
                     'NSPrincipalClass': 'NSApplication',
                     'NSAppleScriptEnabled': False,
                     'CFBundleName': 'DelugeManager',
                     'CFBundleDisplayName': 'DelugeManager',
                 })

