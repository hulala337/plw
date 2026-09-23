@echo off
setlocal
cd /d "%~dp0"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onedir --name RuowoshiTamenV32 --add-data "data;data" --add-data "assets;assets" --add-data "app;app" launcher.py
echo.
echo Portable build: %cd%\dist\RuowoshiTamenV32\RuowoshiTamenV32.exe
pause
