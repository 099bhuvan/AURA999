@echo off
title Launching AURA Personal AI Assistant...
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Please run setup first:
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo [*] Starting AURA Neural Interface...
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0
