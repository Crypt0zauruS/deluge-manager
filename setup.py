from setuptools import setup, find_packages  # type: ignore

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="DelugeManager",
    version="0.3.0",
    description="A Python package for managing torrents with a Bootstrap-based UI.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Crypt0zauruS",
    url="https://github.com/Crypt0zauruS/deluge-manager",
    license="CC BY 4.0",
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
        'gui_scripts': [
            'deluge-manager-gui=deluge_manager.main:main',
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: CC BY 4.0",
        "Operating System :: OS Independent",
        "Intended Audience :: End Users/Desktop",
    ],
    keywords="deluge torrent manager ui bootstrap",
    package_data={
        'deluge_manager': ['*.png', '*.ico', '*.icns'],
    },
    include_package_data=True,
    project_urls={
        "Bug Tracker": "https://github.com/Crypt0zauruS/deluge-manager/issues",
        "Source Code": "https://github.com/Crypt0zauruS/deluge-manager",
    },
)
