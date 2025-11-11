@echo off
REM EduPortal - run_server.bat
REM Creates (if missing) a virtual environment, installs requirements, activates it and starts the Flask app.

REM Change to script directory
cd /d "%~dp0"

REM Create venv if it doesn't exist
if not exist venv (
    echo Creating virtual environment 'venv'...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Ensure Python is on PATH.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Upgrade pip and install requirements
echo Installing/Updating requirements (this may take a moment)...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Start the application
echo Starting EduPortal (local-only) on http://127.0.0.1:5000
python app.py

echo Server stopped.
pause
