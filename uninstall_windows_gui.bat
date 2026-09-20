@echo off
setlocal

echo ================================================================
echo yt-dlp GUI - Desinstalador
echo ================================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\Programs\yt-dlp-gui"
if exist "%~dp0yt-dlp-gui.exe" set "INSTALL_DIR=%~dp0"
echo Este desinstalador remove somente:
echo %INSTALL_DIR%
echo Python, FFmpeg, historico e arquivos baixados nao serao removidos.

if not exist "%INSTALL_DIR%" (
    echo A pasta de instalacao nao foi encontrada:
    echo %INSTALL_DIR%
    pause
    exit /b 0
)

echo.
echo A pasta abaixo sera removida:
echo %INSTALL_DIR%
choice /M "Deseja continuar"
if errorlevel 2 exit /b 0

rmdir /s /q "%INSTALL_DIR%"
if errorlevel 1 (
    echo Nao foi possivel remover a pasta. Feche o app e tente novamente.
    pause
    exit /b 1
)

if exist "%USERPROFILE%\Desktop\yt-dlp-gui.lnk" del /q "%USERPROFILE%\Desktop\yt-dlp-gui.lnk"
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\yt-dlp-gui.lnk" del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\yt-dlp-gui.lnk"
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\yt-dlp-gui" rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\yt-dlp-gui"

echo.
echo Desinstalacao concluida.
echo O historico e os arquivos baixados nao foram removidos.
pause
