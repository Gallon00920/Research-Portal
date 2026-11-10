@echo off
cd /d "%~dp0"
python -m pip install -q -r requirements.txt
echo Starting AID Research Panel on http://127.0.0.1:8765
python backend\server.py
