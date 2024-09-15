#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Run the Python script to check and install missing dependencies
echo "Checking dependencies..."
python check_dependencies.py

# Run the main application
echo "Running the application..."
export PYTHONPATH=$PWD/deluge_manager
python -m deluge_manager.main

# End of script
echo "Application finished."
