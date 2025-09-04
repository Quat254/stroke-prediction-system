@echo off
cd %~dp0
python run_stroke_app.py
if %errorlevel% neq 0 (
    echo Failed to start Stroke Prediction System
    pause
    exit /b %errorlevel%
)
