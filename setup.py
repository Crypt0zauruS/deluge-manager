from setuptools import setup, find_packages  # type: ignore

setup(
    name="DelugeManager",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'ttkbootstrap==1.10.1',
        'requests==2.32.3',
        'keyring==25.3.0',
        'Pillow==10.4.0'
    ],
    entry_points={
        'console_scripts': [
            'deluge-manager=deluge_manager.main:main',
        ],
    },
)
