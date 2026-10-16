@echo off
title PRUBETH AI Studio Pro [Legacy Python v1.89.0 Edition]
cd /d "%~dp0"
echo [LEGACY RUNTIME] Starting PRUBETH AI Studio Pro v1.89.0 (Python/PyQt5)...
set "PY_CMD=%USERPROFILE%\heretic-work\.venv\Scripts\pythonw.exe"
if not exist "%PY_CMD%" set "PY_CMD=pythonw.exe"
start "" "%PY_CMD%" local_ai_studio_pro.py %*
exit /b 0
