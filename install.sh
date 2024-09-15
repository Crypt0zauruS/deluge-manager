#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Check if the virtual environment already exists
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if setuptools is installed
if ! pip show setuptools > /dev/null 2>&1; then
    echo "setuptools is not installed. Installing setuptools..."
    pip install --upgrade setuptools
else
    echo "setuptools is already installed."
fi

# Run the Python script to check and install missing dependencies
echo "Checking and installing missing dependencies..."p
python check_dependencies.py

# Re-activate the virtual environment to ensure it's fully active
echo "Re-activating the virtual environment to ensure it is active..."
source venv/bin/activate

echo "Installation complete."
