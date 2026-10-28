@echo off
setlocal
cd /d "%~dp0"

:: Conda base 環境を探索してアクティベート
if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\miniconda3\Scripts\activate.bat" base
) else if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\anaconda3\Scripts\activate.bat" base
) else if exist "%LOCALAPPDATA%\miniconda3\Scripts\activate.bat" (
    call "%LOCALAPPDATA%\miniconda3\Scripts\activate.bat" base
) else if exist "%LOCALAPPDATA%\anaconda3\Scripts\activate.bat" (
    call "%LOCALAPPDATA%\anaconda3\Scripts\activate.bat" base
) else if exist "C:\ProgramData\miniconda3\Scripts\activate.bat" (
    call "C:\ProgramData\miniconda3\Scripts\activate.bat" base
) else if exist "C:\ProgramData\anaconda3\Scripts\activate.bat" (
    call "C:\ProgramData\anaconda3\Scripts\activate.bat" base
) else (
    call conda activate base >nul 2>nul
)

:: 事前チェック（構文および必須モジュールの確認）
python -c "import customtkinter, pyautogui, PIL" >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Required Python libraries could not be loaded.
    python app.py
    pause
    exit /b 1
)

:: pythonw が利用可能ならコンソールなしでGUIを起動
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0app.py"
) else (
    python "%~dp0app.py"
    if %errorlevel% neq 0 pause
)
