@echo off
setlocal
cd /d "%~dp0"
if not exist .venv (
  echo [1/3] Creating Python virtual environment...
  python -m venv .venv
  if errorlevel 1 goto :python_error
)
call .venv\Scripts\activate.bat
echo [2/3] Installing runtime dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto :pip_error
echo [3/3] Starting History Simulator V3.2...
start "" http://127.0.0.1:52182/
python -m uvicorn app.server:app --host 127.0.0.1 --port 52182
goto :eof
:python_error
echo Python 3.11+ is required for development mode.
pause
exit /b 1
:pip_error
echo Dependency installation failed. Check network access or use the portable build.
pause
exit /b 1
