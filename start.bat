@echo off
chcp 65001 > nul
title GitHub Contributions Bot - Kontrol Paneli

echo ======================================================
echo    GitHub Contributions Otomasyon Yonetim Paneli
echo ======================================================
echo.

:: 1. Python Varlik Kontrolu
echo [*] Python calisma ortami kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [HATA] Sistemde Python bulunamadi!
    echo Lutfen Python 3 yukleyin ve PATH ortam degiskenine ekleyin.
    echo.
    pause
    exit /b 1
)

:: 2. Tarayicida Web Panelini Ac ve Sunucuyu Baslat
echo [*] Web Paneli baslatiliyor: http://localhost:5000
echo [*] Varsayilan tarayici aciliyor...
timeout /t 1 > nul
start http://localhost:5000

echo.
echo [BILGI] Sunucu calisiyor. Paneli kapatmak icin bu pencereyi kapatabilirsiniz.
echo ------------------------------------------------------
python server.py
pause
