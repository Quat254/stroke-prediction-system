@echo off
echo Installing Stroke Prediction System...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Create a virtual environment
cd %~dp0
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)

REM Activate the virtual environment and install dependencies
call venv\Scripts\activate
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

REM Create a desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Stroke Prediction System.lnk'); $Shortcut.TargetPath = '%~dp0StrokeApp.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Save()"

echo.
echo Installation successful!
echo You can now run the Stroke Prediction System by double-clicking on StrokeApp.bat
echo or by using the desktop shortcut.
echo.
pause
