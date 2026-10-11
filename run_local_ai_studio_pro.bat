@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title PRUBETH IDE — Horizon Edition (v3.0.0)

echo ===============================================================================
echo   PRUBETH IDE — Horizon Edition (v3.0.0)
echo   AI-Native Developer Environment (Windows & Linux)
echo ===============================================================================
echo.

:: 1. Check for local virtual environment
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    goto :RUN_APP
)

:: 2. Check for system Python
where python.exe >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3 was not detected on your system PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo and ensure "Add Python to PATH" is checked during installation.
    pause
    exit /b 1
)

:: 3. Test if system Python has required GUI dependencies
python.exe -c "import PyQt5, PyQt5.Qsci, requests" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=python.exe"
    goto :RUN_APP
)

:: 4. If dependencies missing and no .venv, offer automatic setup
echo [!] Virtual environment not found or missing dependencies (PyQt5, QScintilla).
echo [*] Automatically creating local .venv environment...
echo.
python.exe -m venv .venv
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [*] Upgrading pip and installing required packages from requirements.txt...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies into .venv.
    pause
    exit /b 1
)

set "PYTHON_EXE=.venv\Scripts\python.exe"

:RUN_APP
echo [*] Launching PRUBETH IDE via %PYTHON_EXE%...
echo.
"%PYTHON_EXE%" local_ai_studio_pro.py %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo ===============================================================================
    echo [ERROR] PRUBETH IDE terminated with exit code %ERRORLEVEL%.
    echo Review the traceback or output above for diagnosis.
    echo ===============================================================================
    pause
)
endlocal
