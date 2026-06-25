#!/usr/bin/env bash
[ ! -d venv ] && python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q
python app/main.py
