@echo off
echo 🏥 Starting Enhanced Stroke Prediction System...
echo 📊 Enhanced Risk Scoring ^& Visualization Enabled

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo 📦 Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Create database directory
if not exist "database" mkdir database

REM Run the application
echo 🚀 Starting server at http://127.0.0.1:5001
echo 🎯 Enhanced Features:
echo    • Graduated risk scoring system
echo    • Interactive dashboard graphs
echo    • 6-level risk classification
echo    • Detailed score breakdown
echo    • Enhanced visualizations
echo.
echo Press Ctrl+C to stop the server
python app.py
pause
