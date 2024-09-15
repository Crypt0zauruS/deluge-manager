@echo off
REM Change to the directory where the batch file is located
cd /d "%~dp0"

REM Check if the virtual environment already exists
if exist venv (
    echo Virtual environment already exists.
) else (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Check if setuptools is installed
pip show setuptools >nul 2>&1
if %errorlevel% neq 0 (
    echo setuptools is not installed. Installing setuptools...
    pip install --upgrade setuptools
) else (
    echo setuptools is already installed.
)

REM Run the Python script to check and install missing dependencies
echo Checking and installing missing dependencies...
python check_dependencies.py

REM Re-activate the virtual environment to ensure it's fully active
echo Re-activating the virtual environment to ensure it is active...
call venv\Scripts\activate

echo Installation complete.
