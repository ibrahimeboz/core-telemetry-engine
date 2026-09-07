@echo off
chcp 65001 > nul
title VDS Otomatik Kurulum Sihirbazi (Git + Python + Node.js)

echo ===================================================================
echo     VDS Otomatik Gerekli Programlar Kurulum Sihirbazi
echo     (Git, Python 3 ve Node.js LTS Otomatik Indirilir ve Kurulur)
echo ===================================================================
echo.

:: 1. Yonetici Haklari Kontrolu (Admin Rights)
net session >nul 2>&1
if errorlevel 1 (
    echo [!] Bu script sistem geneline program kurabilmek icin Yonetici haklari gerektirir.
    echo [*] Yonetici izni isteniyor...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [✓] Yonetici haklari onaylandi.
echo.

:: Gecici klasor
set "TEMP_DIR=%TEMP%\vds_installer"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: ---------------------------------------------------------------------
:: ADIM 1: Git Kontrolu ve Kurulumu
:: ---------------------------------------------------------------------
echo [*] [1/3] Git kontrol ediliyor...
set "NEED_GIT=1"
git --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('git --version') do echo     [✓] Git zaten yuklu: %%v
    set "NEED_GIT=0"
)

if "%NEED_GIT%"=="1" (
    echo     [-] Git bulunamadi. Resmi 64-bit installer indiriliyor...
    set "GIT_URL=https://github.com/git-for-windows/git/releases/download/v2.46.0.windows.1/Git-2.46.0-64-bit.exe"
    set "GIT_EXE=%TEMP_DIR%\git_setup.exe"

    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%GIT_URL%', '%GIT_EXE%')"

    if exist "%GIT_EXE%" (
        echo     [*] Git sessiz (arkaplanda) kuruluyor, lutfen bekleyin...
        start /wait "" "%GIT_EXE%" /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS
        echo     [✓] Git kurulumu tamamlandi!
        set "PATH=C:\Program Files\Git\cmd;%PATH%"
    ) else (
        echo     [HATA] Git indirilemedi! Lutfen internet baglantinizi kontrol edin.
    )
)

echo.

:: ---------------------------------------------------------------------
:: ADIM 2: Python 3 Kontrolu ve Kurulumu
:: ---------------------------------------------------------------------
echo [*] [2/3] Python kontrol ediliyor...
set "NEED_PY=1"
python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('python --version') do echo     [✓] Python zaten yuklu: %%v
    set "NEED_PY=0"
)

if "%NEED_PY%"=="1" (
    echo     [-] Python bulunamadi. Resmi Python 3.11.9 (64-bit) indiriliyor...
    set "PY_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    set "PY_EXE=%TEMP_DIR%\python_setup.exe"

    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%PY_URL%', '%PY_EXE%')"

    if exist "%PY_EXE%" (
        echo     [*] Python sessiz (PATH eklenerek) kuruluyor, lutfen bekleyin...
        start /wait "" "%PY_EXE%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 SimpleInstall=1
        echo     [✓] Python kurulumu tamamlandi!
        set "PATH=C:\Program Files\Python311;C:\Program Files\Python311\Scripts;%PATH%"
    ) else (
        echo     [HATA] Python indirilemedi! Lutfen internet baglantinizi kontrol edin.
    )
)

echo.

:: ---------------------------------------------------------------------
:: ADIM 3: Node.js LTS Kontrolu ve Kurulumu
:: ---------------------------------------------------------------------
echo [*] [3/3] Node.js kontrol ediliyor...
set "NEED_NODE=1"
node -v >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('node -v') do echo     [✓] Node.js zaten yuklu: %%v
    set "NEED_NODE=0"
)

if "%NEED_NODE%"=="1" (
    echo     [-] Node.js bulunamadi. Resmi Node.js v20 LTS indiriliyor...
    set "NODE_URL=https://nodejs.org/dist/v20.17.0/node-v20.17.0-x64.msi"
    set "NODE_MSI=%TEMP_DIR%\node_setup.msi"

    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%NODE_URL%', '%NODE_MSI%')"

    if exist "%NODE_MSI%" (
        echo     [*] Node.js sessiz (arkaplanda) kuruluyor, lutfen bekleyin...
        msiexec /i "%NODE_MSI%" /qn /norestart
        echo     [✓] Node.js kurulumu tamamlandi!
        set "PATH=C:\Program Files\nodejs;%PATH%"
    ) else (
        echo     [HATA] Node.js indirilemedi! Lutfen internet baglantinizi kontrol edin.
    )
)

echo.

:: ---------------------------------------------------------------------
:: Gecici Dosyalari Temizle
:: ---------------------------------------------------------------------
rmdir /s /q "%TEMP_DIR%" >nul 2>&1

:: ---------------------------------------------------------------------
:: Kurulum Ozeti & Dogrulama
:: ---------------------------------------------------------------------
echo ===================================================================
echo                     KURULUM VE DURUM OZETI
echo ===================================================================

git --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('git --version') do echo   • Git Durumu    : %%i
) else (
    echo   • Git Durumu    : Yuklendi (Terminali yeniden baslatinca aktiflesir)
)

python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('python --version') do echo   • Python Durumu : %%i
) else (
    echo   • Python Durumu : Yuklendi (Terminali yeniden baslatinca aktiflesir)
)

node -v >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('node -v') do echo   • Node.js Durumu: Node %%i
) else (
    echo   • Node.js Durumu: Yuklendi (Terminali yeniden baslatinca aktiflesir)
)

echo ===================================================================
echo.
echo [Tebrikler] VDS ortami bot calistirmak icin tamamen hazir hale getirildi!
echo.
echo Sonraki Adimlar:
echo   1. Eger yeni repo baslatmak istiyorsaniz: setup_and_push.bat calistirin.
echo   2. Web Yonetim Panelini acmak istiyorsaniz: start.bat calistirin.
echo.
pause
