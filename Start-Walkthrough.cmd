@echo off
powershell.exe -NoProfile -STA -File "%~dp0pipeline\settings-ui.ps1"
if errorlevel 1 pause
