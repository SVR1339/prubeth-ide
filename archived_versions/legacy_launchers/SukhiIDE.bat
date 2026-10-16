@echo off
setlocal enabledelayedexpansion
title PRUBETH IDE — Horizon Edition Launcher
cd /d "%~dp0"

:: 1. If standalone executable is installed, launch it directly
if exist "PrubethIDE.exe" (
    start "" "PrubethIDE.exe" %*
    exit /b 0
)
if exist "SukhiIDE.exe" (
    start "" "SukhiIDE.exe" %*
    exit /b 0
)
if exist "SoNaive.exe" (
    start "" "SoNaive.exe" %*
    exit /b 0
)

:: 2. Locate available Python runtime
set "PY_CMD="
set "PY_CON="

if exist ".venv\Scripts\pythonw.exe" (
    set "PY_CMD=.venv\Scripts\pythonw.exe"
    set "PY_CON=.venv\Scripts\python.exe"
) else if exist "..\.venv\Scripts\pythonw.exe" (
    set "PY_CMD=..\.venv\Scripts\pythonw.exe"
    set "PY_CON=..\.venv\Scripts\python.exe"
) else (
    where pythonw.exe >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_CMD=pythonw.exe"
        set "PY_CON=python.exe"
    ) else (
        where python.exe >nul 2>&1
        if !errorlevel! equ 0 (
            set "PY_CMD=python.exe"
            set "PY_CON=python.exe"
        )
    )
)

if "!PY_CMD!"=="" (
    echo [ERROR] Python 3 was not detected on your system.
    echo Please install Python 3.10+ from https://python.org/
    mshta "javascript:alert('PRUBETH Launcher Error:\n\nPython 3 is not installed or not in PATH.\nPlease install Python 3.10+ from https://python.org');close();"
    pause
    exit /b 1
)

:: 3. Verify application file existence
if not exist "local_ai_studio_pro.py" (
    echo [ERROR] local_ai_studio_pro.py was not found in %~dp0
    mshta "javascript:alert('PRUBETH Launcher Error:\n\nApplication core file (local_ai_studio_pro.py) was not found in installation folder.');close();"
    pause
    exit /b 1
)

:: 4. Verify core dependencies
if exist "!PY_CON!" (
    "!PY_CON!" -c "import PyQt5, requests" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] Required libraries (PyQt5, requests) are not installed.
        echo Run: pip install -r requirements.txt
        mshta "javascript:alert('PRUBETH Launcher Warning:\n\nRequired libraries (PyQt5, requests) were not found in Python environment.\nPlease run: pip install -r requirements.txt');close();"
    )
)

:: 5. Launch application
start "" "!PY_CMD!" local_ai_studio_pro.py %*
exit /b 0
