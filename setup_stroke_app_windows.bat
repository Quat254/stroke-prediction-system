@echo off
echo ===================================================
echo Stroke Prediction System - Windows Setup
echo ===================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from python.org/downloads
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    echo After installing Python, run this setup again.
    pause
    exit /b 1
)

echo Python is installed. Setting up the application...
echo.

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Stroke Prediction System.lnk'); $Shortcut.TargetPath = '%~dp0StrokeApp.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"

echo.
echo ===================================================
echo Setup completed successfully!
echo.
echo You can now run the Stroke Prediction System by:
echo  1. Double-clicking on StrokeApp.bat in this folder
echo  2. Using the desktop shortcut that was created
echo ===================================================
echo.

pause
