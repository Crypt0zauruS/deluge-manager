@echo off
REM Change to the directory where the batch file is located
cd /d "%~dp0"

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Check if all dependencies are installed
echo Checking dependencies...
python check_dependencies.py

REM Run the main application
echo Running the application...
set PYTHONPATH=%cd%\deluge_manager
python -m deluge_manager.main

REM End of script
pause
