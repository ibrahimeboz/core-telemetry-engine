@echo off
chcp 65001 > nul
title Telemetry Engine - Diagnostic Studio

echo ======================================================
echo    Core Telemetry Engine - Diagnostic Studio
echo ======================================================
echo.

echo [*] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python not found in system PATH.
    echo Please install Python 3.9 or newer.
    echo.
    pause
    exit /b 1
)

echo [*] Launching Diagnostic Studio at http://localhost:5000...
timeout /t 1 > nul
start http://localhost:5000

echo.
echo [INFO] Studio server running. Press Ctrl+C or close this window to exit.
echo ------------------------------------------------------
python server.py
pause
