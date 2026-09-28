@echo off
cd /d "%~dp0"
title Jarvis

rem Find a Python that really runs. Windows ships a fake "python" that only
rem opens the Microsoft Store, so check the version instead of just the name.
set PY=
python --version >nul 2>nul && set PY=python
if not defined PY (py --version >nul 2>nul && set PY=py)
if not defined PY (
  echo Python is not installed on this computer.
  echo.
  echo 1. Download it from https://www.python.org/downloads/
  echo 2. Run the installer and tick "Add python.exe to PATH" at the bottom
  echo 3. Double-click START_JARVIS.bat again
  pause
  exit /b
)

echo Getting Jarvis ready (the first time takes a minute)...
%PY% -m pip install --quiet --disable-pip-version-check anthropic SpeechRecognition
if errorlevel 1 (
  echo.
  echo Could not install what Jarvis needs. Check your internet connection
  echo and try again.
  pause
  exit /b
)

rem Microphone and voice extras. If these fail, Jarvis still works by typing.
%PY% -m pip install --quiet --disable-pip-version-check PyAudio pywin32 >nul 2>nul

%PY% jarvis.py
pause
