@echo off
setlocal
cd /d "%~dp0.."
if "%OPENAI_API_KEY%"=="" (
  echo [ERROR] OPENAI_API_KEY is not set.
  exit /b 1
)
python art-pipeline\vision_art_director.py %*
if errorlevel 1 exit /b %errorlevel%
python art-pipeline\production_report.py %*
