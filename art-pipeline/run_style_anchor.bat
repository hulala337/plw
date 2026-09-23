@echo off
setlocal
cd /d "%~dp0.."

if "%OPENAI_API_KEY%"=="" (
  echo [ERROR] OPENAI_API_KEY is not set.
  echo Set it in PowerShell first:
  echo   $env:OPENAI_API_KEY="..."
  exit /b 1
)

python art-pipeline\batch.py --ids B01,B02,B03,B04,B07,B11,C01,C02,C03,E01
if errorlevel 1 exit /b 1

echo.
echo [NEXT] Review candidates:
echo   python art-pipeline\review_server.py
echo.
echo [NEXT] After approval:
echo   python art-pipeline\integrate.py
