@echo off
start "" pwsh.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -Command ^
  "Start-Process python -ArgumentList 'C:\Users\Lee\OneDrive\Code\dcf\dcf.py' -WindowStyle Hidden"
REM This script starts the dcf.py script using PowerShell with Python.
REM It runs in the background without showing a console window.