@echo off
chcp 65001 > nul
title GitHub Otomatik Kurulum ve Push Sihirbazi

echo ====================================================================
echo             GitHub Contributions Bot - Kurulum ve Push
echo ====================================================================
echo.

:: 1. ADIM: Git Programinin Tespiti
echo [*] [1/6] Git kontrol ediliyor...
set "GIT_CMD=git"
git --version >nul 2>&1
if errorlevel 1 (
    if exist "C:\Program Files\Git\cmd\git.exe" (
        set "GIT_CMD=C:\Program Files\Git\cmd\git.exe"
        set "PATH=C:\Program Files\Git\cmd;%PATH%"
        echo     - Git 'Program Files' altinda bulundu ve PATH'e eklendi.
    ) else if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" (
        set "GIT_CMD=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
        set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
        echo     - Git 'LocalAppData' altinda bulundu ve PATH'e eklendi.
    ) else (
        echo.
        echo [HATA] Sistemde Git programi bulunamadi!
        echo Lutfen Git'i kurun: https://git-scm.com/downloads
        echo.
        pause
        exit /b 1
    )
)
echo     - Git hazir.

:: 2. ADIM: Git Kimlik Kontrolu (config.json'dan Otomatik Oku)
echo.
echo [*] [2/6] Kullanici kimligi dogrulaniyor...
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
    echo     - Git e-postaniz tespit edilemedi.
    set /p GIT_EMAIL="Lutfen GitHub e-postanizi girin: "
)

if "%GIT_NAME%"=="" (
    echo     - Git kullanici adiniz tespit edilemedi.
    set /p GIT_NAME="Lutfen GitHub kullanici adinizi girin: "
)

"%GIT_CMD%" config --global user.email "%GIT_EMAIL%"
"%GIT_CMD%" config --global user.name "%GIT_NAME%"
echo     - Kimlik baglandi: %GIT_NAME% ^<%GIT_EMAIL%^>

:: 3. ADIM: Depoyu Baslatma (git init)
echo.
echo [*] [3/6] Yerel Git deposu kontrol ediliyor...
if not exist ".git" (
    "%GIT_CMD%" init -b main
    echo     - Yerel depo 'main' daliyla baslatildi.
) else (
    "%GIT_CMD%" branch -M main >nul 2>&1
    echo     - Yerel depo hazir.
)

:: 4. ADIM: Uzak Depo Baglantisi (Remote Origin Kontrolu)
echo.
echo [*] [4/6] Uzak GitHub deposu baglantisi kontrol ediliyor...
set "CURRENT_ORIGIN="
"%GIT_CMD%" remote get-url origin >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%u in ('"%GIT_CMD%" remote get-url origin') do set "CURRENT_ORIGIN=%%u"
)

:: Bagli origin varsa erisilebilir mi test et
if defined CURRENT_ORIGIN (
    echo     - Mevcut bagli remote: %CURRENT_ORIGIN%
    "%GIT_CMD%" ls-remote origin >nul 2>&1
    if errorlevel 1 (
        echo.
        echo     [!] UYARI: Mevcut bagli repo GitHub'da artik bulunamadi veya silinmis!
        echo     Yeni olusturdugunuz deponun linkini baglamamiz gerekiyor.
        goto ask_new_url
    ) else (
        echo.
        set /p CHANGE_ORIGIN="    Mevcut repo URL'sini degistirmek istiyor musunuz? [E/H, varsayilan H]: "
        if /i "%CHANGE_ORIGIN%"=="E" goto ask_new_url
        goto step_commit
    )
) else (
    goto ask_new_url
)

:ask_new_url
echo.
echo ====================================================================
echo               YENI GITHUB REPOSITORY BAGLANTISI
echo ====================================================================
echo GitHub'da actiginiz YENI bos repository linkini yapistirin:
echo (Ornek: https://github.com/%GIT_NAME%/yeni-repo.git)
echo ====================================================================
:input_url
set "REPO_URL="
set /p REPO_URL="Repo URL: "

if not defined REPO_URL goto warn_empty
if "%REPO_URL%"=="" goto warn_empty
if "%REPO_URL%"==" " goto warn_empty

:: Tirnak ve bosluklari temizle
set "REPO_URL=%REPO_URL:"=%"
set "REPO_URL=%REPO_URL: =%"

"%GIT_CMD%" remote remove origin >nul 2>&1
"%GIT_CMD%" remote add origin "%REPO_URL%"
echo.
echo     - Yeni uzak depo baglandi: %REPO_URL%
goto step_commit

:warn_empty
echo.
echo [UYARI] URL bos birakilamaz! Lutfen gecerli bir GitHub repo linki girin.
goto input_url

:: 5. ADIM: Dosyalari Sahneleme ve Commit
:step_commit
echo.
echo [*] [5/6] Proje dosyalari sahneleniyor ve commit olusturuluyor...
"%GIT_CMD%" add -A

"%GIT_CMD%" rev-parse --verify HEAD >nul 2>&1
if errorlevel 1 (
    "%GIT_CMD%" commit -m "feat: initial project structure and baseline configuration"
) else (
    "%GIT_CMD%" status --porcelain | findstr "^" >nul 2>&1
    if not errorlevel 1 (
        "%GIT_CMD%" commit -m "feat: update project files and baseline configuration"
    ) else (
        echo     - Yeni dosya degisikligi yok, mevcut commit kullanilacak.
    )
)

:: 6. ADIM: GitHub'a Yukleme (git push)
echo.
echo [*] [6/6] GitHub'a yukleniyor (git push -u origin main --force)...
"%GIT_CMD%" push -u origin main --force

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo  [HATA] Push islemi sirasinda bir sorun olustu!
    echo.
    echo  Olası Sebepler:
    echo   1. Girdiginiz repo URL'si hatali olabilir.
    echo   2. GitHub tarayicinizda giris onayi / yetkilendirme bekliyor olabilir.
    echo   3. Repoyu henuz GitHub uzerinde olusturmamis olabilirsiniz.
    echo ====================================================================
) else (
    echo.
    echo ====================================================================
    echo  [TEBRIKLER] Tum proje dosyalari basariyla GitHub'a yuklendi!
    echo ====================================================================
    echo  - GitHub Actions her gun rastgele zaman pencerelerinde dogal
    echo    commit'ler uretmeye baslayacaktir.
    echo  - Web panelini baslatmak icin 'start.bat' dosyasini calistirabilirsiniz.
    echo ====================================================================
)

echo.
pause
