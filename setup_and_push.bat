@echo off
chcp 65001 > nul
title Core Telemetry Engine - Repository Setup & Push

echo ====================================================================
echo             Core Telemetry Engine - Repository Deployment
echo ====================================================================
echo.

:: 1. Git Executable Check
echo [*] [1/6] Checking Git environment...
set "GIT_CMD=git"
git --version >nul 2>&1
if errorlevel 1 (
    if exist "C:\Program Files\Git\cmd\git.exe" (
        set "GIT_CMD=C:\Program Files\Git\cmd\git.exe"
        set "PATH=C:\Program Files\Git\cmd;%PATH%"
        echo     - Git located in Program Files and added to PATH.
    ) else if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" (
        set "GIT_CMD=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
        set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
        echo     - Git located in LocalAppData and added to PATH.
    ) else (
        echo.
        echo [ERROR] Git is not installed or not in PATH.
        echo Please download Git: https://git-scm.com/downloads
        echo.
        pause
        exit /b 1
    )
)
echo     - Git ready.

:: 2. Identity Verification
echo.
echo [*] [2/6] Verifying committer identity...
set "GIT_EMAIL="
set "GIT_NAME="

python --version >nul 2>&1
if not errorlevel 1 (
    if exist "config.json" (
        for /f "tokens=*" %%i in ('python -c "import json; c=json.load(open('config.json', encoding='utf-8')); print(c.get('github',{}).get('email',''))" 2^>nul') do set GIT_EMAIL=%%i
        for /f "tokens=*" %%i in ('python -c "import json; c=json.load(open('config.json', encoding='utf-8')); print(c.get('github',{}).get('username',''))" 2^>nul') do set GIT_NAME=%%i
    )
)

if "%GIT_EMAIL%"=="" (
    for /f "tokens=*" %%i in ('"%GIT_CMD%" config user.email 2^>nul') do set GIT_EMAIL=%%i
)
if "%GIT_NAME%"=="" (
    for /f "tokens=*" %%i in ('"%GIT_CMD%" config user.name 2^>nul') do set GIT_NAME=%%i
)

if "%GIT_EMAIL%"=="" (
    echo     - Committer email not detected.
    set /p GIT_EMAIL="Enter GitHub email: "
)

if "%GIT_NAME%"=="" (
    echo     - Committer username not detected.
    set /p GIT_NAME="Enter GitHub username: "
)

"%GIT_CMD%" config --global user.email "%GIT_EMAIL%"
"%GIT_CMD%" config --global user.name "%GIT_NAME%"
echo     - Identity configured: %GIT_NAME% ^<%GIT_EMAIL%^>

:: 3. Repository Initialization
echo.
echo [*] [3/6] Initializing local repository branch...
if not exist ".git" (
    "%GIT_CMD%" init -b main
    echo     - Local repository initialized with branch 'main'.
) else (
    "%GIT_CMD%" branch -M main >nul 2>&1
    echo     - Local branch confirmed as 'main'.
)

:: 4. Remote Origin Verification
echo.
echo [*] [4/6] Verifying remote repository origin...
set "CURRENT_ORIGIN="
"%GIT_CMD%" remote get-url origin >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%u in ('"%GIT_CMD%" remote get-url origin') do set "CURRENT_ORIGIN=%%u"
)

if defined CURRENT_ORIGIN (
    echo     - Connected remote origin: %CURRENT_ORIGIN%
    "%GIT_CMD%" ls-remote origin >nul 2>&1
    if errorlevel 1 (
        echo.
        echo     [!] Remote origin unreachable. Reconfiguration required.
        goto ask_new_url
    ) else (
        echo.
        set /p CHANGE_ORIGIN="    Change repository URL? [y/N]: "
        if /i "%CHANGE_ORIGIN%"=="y" goto ask_new_url
        goto step_commit
    )
) else (
    goto ask_new_url
)

:ask_new_url
echo.
echo ====================================================================
echo               REMOTE REPOSITORY CONFIGURATION
echo ====================================================================
echo Enter target GitHub repository URL:
echo (Example: https://github.com/%GIT_NAME%/core-telemetry-engine.git)
echo ====================================================================
:input_url
set "REPO_URL="
set /p REPO_URL="Repo URL: "

if not defined REPO_URL goto warn_empty
if "%REPO_URL%"=="" goto warn_empty

set "REPO_URL=%REPO_URL:"=%"
set "REPO_URL=%REPO_URL: =%"

"%GIT_CMD%" remote remove origin >nul 2>&1
"%GIT_CMD%" remote add origin "%REPO_URL%"
echo.
echo     - Remote origin set to: %REPO_URL%
goto step_commit

:warn_empty
echo.
echo [WARNING] URL cannot be empty. Please enter a valid URL.
goto input_url

:: 5. Staging & Baseline Commit
:step_commit
echo.
echo [*] [5/6] Running unit tests and staging project files...
python -m unittest discover tests
if errorlevel 1 (
    echo [ERROR] Unit tests failed. Aborting commit.
    pause
    exit /b 1
)

"%GIT_CMD%" add -A

"%GIT_CMD%" rev-parse --verify HEAD >nul 2>&1
if errorlevel 1 (
    "%GIT_CMD%" commit -m "feat(core): initial architecture and baseline telemetry engine"
) else (
    "%GIT_CMD%" status --porcelain | findstr "^" >nul 2>&1
    if not errorlevel 1 (
        "%GIT_CMD%" commit -m "feat(telemetry): update engine architecture and diagnostic suite"
    ) else (
        echo     - Working tree clean. Using existing commit.
    )
)

:: 6. Push to Origin
echo.
echo [*] [6/6] Pushing to remote branch (git push -u origin main)...
"%GIT_CMD%" push -u origin main

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo  [ERROR] Git push encountered an issue.
    echo  Check remote permissions and repository existence.
    echo ====================================================================
) else (
    echo.
    echo ====================================================================
    echo  [SUCCESS] Core Telemetry Engine successfully deployed!
    echo ====================================================================
    echo  - CI / Diagnostics & Benchmark Suite active on GitHub Actions.
    echo  - Launch local monitoring console via 'start.bat'.
    echo ====================================================================
)

echo.
pause
