@echo off
set "TARGET_DIR=%~dp0"
if "%~1" neq "" set "TARGET_DIR=%~f1"

:: If --restart or -r argument is passed, cleanly terminate old instances
if "%1"=="--restart" (
    taskkill /F /IM "PRUBETH.exe" >nul 2>&1
    timeout /t 1 /nobreak >nul
)

:: Clear stale locks
if exist "%APPDATA%\PRUBETH\code.lock" (
    tasklist /FI "IMAGENAME eq PRUBETH.exe" 2>NUL | find /I /N "PRUBETH.exe">NUL
    if errorlevel 1 del /f /q "%APPDATA%\PRUBETH\code.lock" >nul 2>&1
)

:: Launch with Dedicated High Priority and GPU acceleration
start "" /high "E:\PRUBETH IDE\PRUBETH.exe" --enable-gpu-rasterization --enable-zero-copy --ignore-gpu-blocklist --disable-background-timer-throttling --disable-renderer-backgrounding "%TARGET_DIR%"
