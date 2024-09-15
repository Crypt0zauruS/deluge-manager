from setuptools import setup, find_packages # type: ignore

setup(
    name="DelugeManager",
    version="0.2.0",
    description="A Python package for managing torrents with a Bootstrap-based UI.",
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
    },
    python_requires='>=3.7',  
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: CC BY 4.0",
        "Operating System :: OS Independent",
    ],
    package_data={
        '': ['*.png', '*.ico', '*.icns'],  
    },
    include_package_data=True,  
)
