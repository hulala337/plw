@echo off
setlocal
cd /d "%~dp0"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
python -m pip install -r requirements.txt

echo.
echo [1/3] Downloading/registering local historical image assets...
python assets\history\download_historical_assets.py
if errorlevel 1 (
  echo.
  echo Historical asset bootstrap FAILED.
  echo Check network access to upload.wikimedia.org, then rerun.
  pause
  exit /b 1
)

echo.
echo [2/3] Validating local assets, data and simulation...
python validate.py
if errorlevel 1 (
  echo.
  echo V3.2 validation FAILED.
  pause
  exit /b 1
)

echo.
echo [3/3] Building portable package...
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onedir --name RuowoshiTamenV32 --add-data "data;data" --add-data "assets;assets" --add-data "app;app" launcher.py
if errorlevel 1 (
  echo.
  echo PyInstaller build FAILED.
  pause
  exit /b 1
)

echo.
echo Portable build: %cd%\dist\RuowoshiTamenV32\RuowoshiTamenV32.exe
echo Local historical assets are included under assets\history.
pause
