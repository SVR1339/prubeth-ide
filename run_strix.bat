@echo off
title PRUBETH IDE - Strix Security Runner
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_strix.ps1" %*
pause
