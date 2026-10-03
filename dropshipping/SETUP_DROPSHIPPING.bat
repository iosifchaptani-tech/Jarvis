@echo off
rem Double-click to set up (or refresh) the dropshipping agents. Safe to run again.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
echo.
pause
