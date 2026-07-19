@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo EduMate one-click startup
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_and_run.ps1"
echo.
pause
