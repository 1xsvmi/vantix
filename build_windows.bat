@echo off
setlocal EnableDelayedExpansion
echo ============================
echo    VANTIX Windows Builder
echo ============================

:: Create venv if missing
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install requirements
echo Installing requirements...
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-windows.txt

:: Build executable
echo Building Vantix.exe...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name Vantix ^
    --icon=app\assets\icon.ico ^
    --add-data "app\assets;app\assets" ^
    --hidden-import PyQt6.sip ^
    --hidden-import psutil ^
    --hidden-import requests ^
    app\main.py

if exist "dist\Vantix.exe" (
    echo.
    echo [SUCCESS] Build complete: dist\Vantix.exe
) else (
    echo [ERROR] Build failed.
    exit /b 1
)
