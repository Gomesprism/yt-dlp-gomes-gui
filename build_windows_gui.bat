@echo off
setlocal

cls
echo ================================================================
echo yt-dlp GUI - Build para Windows
echo Feito por IA
echo ================================================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo Python nao foi encontrado.
    echo Instalando Python 3.12 via winget...
    winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo Falha ao instalar Python.
        echo Instale o Python 3.12 manualmente e rode este arquivo novamente.
        pause
        exit /b 1
    )
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo FFmpeg nao foi encontrado.
    echo Instalando FFmpeg via winget...
    winget install --id Gyan.Dev.FFmpeg -e --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo Falha ao instalar FFmpeg.
        echo Instale o FFmpeg manualmente e rode este arquivo novamente.
        pause
        exit /b 1
    )
)

echo Atualizando pip...
py -m pip install --upgrade pip
if errorlevel 1 (
    echo Falha ao atualizar pip.
    pause
    exit /b 1
)

echo Instalando dependencias do projeto...
py -m pip install --upgrade pyinstaller
py -m pip install -e ".[gui]"
if errorlevel 1 (
    echo Falha na instalacao das dependencias.
    pause
    exit /b 1
)

echo Gerando executavel da interface...
py -m PyInstaller --onefile --name yt-dlp-gui --windowed --icon devscripts\logo.ico yt_dlp\gui.py
if errorlevel 1 (
    echo Falha na compilacao do executavel.
    pause
    exit /b 1
)

copy /y uninstall_windows_gui.bat dist\uninstall_windows_gui.bat >nul

echo.
echo ================================================================
echo Build concluido com sucesso.
echo Arquivo gerado: dist\yt-dlp-gui.exe
echo Para abrir o assistente de instalacao:
    echo py -m yt_dlp.gui_installer
    echo.
    echo Caso o comando acima nao funcione, rode:
    echo py -m pip install -e ".[gui]"
    echo ================================================================
echo.

pause
