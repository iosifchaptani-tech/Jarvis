@echo off
cd /d "%~dp0"
title Jarvis

set PY=python
where python >nul 2>nul || set PY=py

echo Getting Jarvis ready (the first time takes a minute)...
%PY% -m pip install --quiet --disable-pip-version-check anthropic SpeechRecognition
if errorlevel 1 (
  echo.
  echo Could not install what Jarvis needs.
  echo Make sure Python is installed from python.org and that you ticked
  echo "Add python.exe to PATH" during install.
  pause
  exit /b
)

rem Microphone and voice extras. If these fail, Jarvis still works by typing.
%PY% -m pip install --quiet --disable-pip-version-check PyAudio pywin32 >nul 2>nul

%PY% jarvis.py
pause
