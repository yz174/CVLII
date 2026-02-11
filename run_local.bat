@echo off
REM Quick launch script for Windows

echo ============================================
echo   TUI Resume - Local Test Launcher
echo ============================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [Step 1/3] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [Step 2/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [Step 3/3] Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Setup Complete! Launching TUI...
echo ============================================
echo.
echo Press Ctrl+C to exit
echo.

REM Launch the app
python -m src.tui_resume.app

pause
