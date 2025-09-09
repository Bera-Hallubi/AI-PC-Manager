@echo off
echo AI PC Manager - GUI Launcher
echo ============================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8+ and add it to PATH.
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "main.py" (
    echo Error: main.py not found. Please run this script from the AI PC Manager directory.
    pause
    exit /b 1
)

REM Run the GUI launcher
echo Starting AI PC Manager GUI...
python launch_gui.py

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo An error occurred. Press any key to exit.
    pause >nul
)
