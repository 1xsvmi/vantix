#!/usr/bin/env bash
set -e
echo "================================"
echo "    VANTIX Linux Builder"
echo "================================"

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Building Vantix binary..."
pyinstaller \
    --onefile \
    --windowed \
    --name Vantix \
    --add-data "app/assets:app/assets" \
    --hidden-import PyQt6.sip \
    --hidden-import psutil \
    --hidden-import requests \
    app/main.py

if [ -f "dist/Vantix" ]; then
    chmod +x dist/Vantix
    echo ""
    echo "[SUCCESS] Build complete: dist/Vantix"
    echo "Run with: ./dist/Vantix"
else
    echo "[ERROR] Build failed."
    exit 1
fi
