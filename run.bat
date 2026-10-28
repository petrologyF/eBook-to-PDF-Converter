@echo off
cd /d "%~dp0"
start "" pythonw app.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start with pythonw. Attempting standard python...
    python app.py
    pause
)
