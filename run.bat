@echo off
call venv\Scripts\activate.bat 2>nul || (python -m venv venv && call venv\Scripts\activate.bat)
pip install -r requirements.txt -q
python app\main.py
