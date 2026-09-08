@echo off
chcp 65001 > nul
title Telemetry Engine Server Setup (Git + Python + Node.js)

echo ===================================================================
echo     Core Telemetry Engine - Server Environment Setup
echo     (Installs Git, Python 3.11, and Node.js LTS)
echo ===================================================================
echo.

:: Administrator check
net session >nul 2>&1
if errorlevel 1 (
    echo [!] Administrator privileges required for system installation.
    echo [*] Requesting elevation...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [OK] Administrator rights confirmed.
echo.

set "TEMP_DIR=%TEMP%\telemetry_installer"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: Step 1: Git
echo [*] [1/3] Checking Git...
set "NEED_GIT=1"
git --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('git --version') do echo     [OK] Git installed: %%v
    set "NEED_GIT=0"
)

if "%NEED_GIT%"=="1" (
    echo     [-] Git not found. Downloading official 64-bit installer...
    set "GIT_URL=https://github.com/git-for-windows/git/releases/download/v2.46.0.windows.1/Git-2.46.0-64-bit.exe"
    set "GIT_EXE=%TEMP_DIR%\git_setup.exe"

    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%GIT_URL%', '%GIT_EXE%')"

    if exist "%GIT_EXE%" (
        echo     [*] Installing Git silently...
        start /wait "" "%GIT_EXE%" /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS
        echo     [OK] Git installation complete.
        set "PATH=C:\Program Files\Git\cmd;%PATH%"
    ) else (
        echo     [ERROR] Git download failed.
    )
)

echo.

:: Step 2: Python
echo [*] [2/3] Checking Python...
set "NEED_PY=1"
python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('python --version') do echo     [OK] Python installed: %%v
    set "NEED_PY=0"
)

if "%NEED_PY%"=="1" (
    echo     [-] Python not found. Downloading Python 3.11.9...
    set "PY_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    set "PY_EXE=%TEMP_DIR%\python_setup.exe"

    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%PY_URL%', '%PY_EXE%')"

    if exist "%PY_EXE%" (
        echo     [*] Installing Python silently with PATH configured...
        start /wait "" "%PY_EXE%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 SimpleInstall=1
        echo     [OK] Python installation complete.
        set "PATH=C:\Program Files\Python311;C:\Program Files\Python311\Scripts;%PATH%"
    ) else (
        echo     [ERROR] Python download failed.
    )
)

echo.

:: Step 3: Node.js
echo [*] [3/3] Checking Node.js...
set "NEED_NODE=1"
node -v >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('node -v') do echo     [OK] Node.js installed: %%v
    set "NEED_NODE=0"
)

if "%NEED_NODE%"=="1" (
    echo     [-] Node.js not found. Downloading Node.js v20 LTS...
    set "NODE_URL=https://nodejs.org/dist/v20.17.0/node-v20.17.0-x64.msi"
    set "NODE_MSI=%TEMP_DIR%\node_setup.msi"

    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%NODE_URL%', '%NODE_MSI%')"

    if exist "%NODE_MSI%" (
        echo     [*] Installing Node.js silently...
        msiexec /i "%NODE_MSI%" /qn /norestart
        echo     [OK] Node.js installation complete.
        set "PATH=C:\Program Files\nodejs;%PATH%"
    ) else (
        echo     [ERROR] Node.js download failed.
    )
)

echo.

rmdir /s /q "%TEMP_DIR%" >nul 2>&1

echo ===================================================================
echo                     INSTALLATION SUMMARY
echo ===================================================================

git --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('git --version') do echo   - Git Status    : %%i
) else (
    echo   - Git Status    : Installed (restart terminal to activate)
)

python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('python --version') do echo   - Python Status : %%i
) else (
    echo   - Python Status : Installed (restart terminal to activate)
)

node -v >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('node -v') do echo   - Node.js Status: Node %%i
) else (
    echo   - Node.js Status: Installed (restart terminal to activate)
)

echo ===================================================================
echo.
echo [INFO] Server environment is configured for Core Telemetry Engine.
echo.
echo Available commands:
echo   - Run 'setup_and_push.bat' to initialize repository sync.
echo   - Run 'start.bat' to launch Telemetry Diagnostic Studio.
echo.
pause
