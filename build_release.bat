@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "ROOT=%CD%"
set "VERSION_FILE=%ROOT%\VERSION.txt"
set "VENV=%ROOT%\.venv"
set "PY=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\pip.exe"
set "DIST=%ROOT%\dist"
set "BUILD=%ROOT%\build"
set "RELEASE=%ROOT%\release"
set "SIGN_DIR=%USERPROFILE%\.pelican_workbench\signing"
set "PRIVATE_KEY=%SIGN_DIR%\private.key"
set "ISCC="
set "SIGNTOOL=%SIGNTOOL_PATH%"

if not exist "%VERSION_FILE%" (
  echo [ERROR] VERSION.txt not found.
  goto :fail
)
set /p VERSION=<"%VERSION_FILE%"

echo.
echo ============================================================
echo  PELICAN WORKBENCH V3.2.3 - RELIABLE WINDOWS RELEASE
echo ============================================================
echo [INFO] Version: %VERSION%
echo [INFO] Build engine: PyInstaller one-file
echo [INFO] Why: Windows/pywebview packaging is more reliable with PyInstaller.
echo.

where py >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python Launcher ^(py.exe^) not found. Install Python 3.11/3.12 x64.
  goto :fail
)

if not exist "%PY%" (
  echo [1/8] Creating isolated virtual environment...
  py -3 -m venv "%VENV%" || goto :fail
)

call "%PY%" -m pip install --upgrade pip setuptools wheel || goto :fail
call "%PIP%" install -r "%ROOT%\requirements.txt" || goto :fail
call "%PIP%" install --upgrade "pyinstaller>=6.16,<7" || goto :fail

if not exist "%SIGN_DIR%" mkdir "%SIGN_DIR%"
if not exist "%PRIVATE_KEY" (
  echo [2/8] Creating your local signing key...
  echo [WARN] Private key stays under %SIGN_DIR% and is never packaged.
  call "%PY%" "%ROOT%\tools\sign_release.py" --root "%ROOT%" --version "%VERSION%" --private-key "%PRIVATE_KEY%" || goto :fail
) else (
  echo [2/8] Signing protected assets with existing local key...
  call "%PY%" "%ROOT%\tools\sign_release.py" --root "%ROOT%" --version "%VERSION%" --private-key "%PRIVATE_KEY%" || goto :fail
)

if exist "%DIST%" rmdir /s /q "%DIST%"
if exist "%BUILD%" rmdir /s /q "%BUILD%"
if exist "%RELEASE%" rmdir /s /q "%RELEASE%"
mkdir "%DIST%"
mkdir "%BUILD%"
mkdir "%RELEASE%"

echo [3/8] Building one-file Windows EXE with PyInstaller...
call "%PY%" -m PyInstaller --noconfirm --clean "%ROOT%\PelicanWorkbench.spec" || goto :fail

if not exist "%DIST%\PelicanWorkbench.exe" (
  echo [ERROR] PyInstaller did not produce PelicanWorkbench.exe.
  goto :fail
)

echo [4/8] Optional Authenticode signing...
if not defined SIGNTOOL (
  for /f "delims=" %%I in ('where signtool.exe 2^>nul') do if not defined SIGNTOOL set "SIGNTOOL=%%I"
)
if defined SIGNTOOL if defined PFX_PATH if defined PFX_PASSWORD (
  if defined TIMESTAMP_URL (
    "%SIGNTOOL%" sign /fd SHA256 /f "%PFX_PATH%" /p "%PFX_PASSWORD%" /tr "%TIMESTAMP_URL%" /td SHA256 "%DIST%\PelicanWorkbench.exe" || goto :fail
  ) else (
    "%SIGNTOOL%" sign /fd SHA256 /f "%PFX_PATH%" /p "%PFX_PASSWORD%" "%DIST%\PelicanWorkbench.exe" || goto :fail
  )
) else echo [INFO] No Authenticode certificate configured.

echo [5/8] Compiling Inno Setup installer...
for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do if not defined ISCC set "ISCC=%%I"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC (
  echo [ERROR] Inno Setup 6 was not found.
  goto :fail
)
call "%ISCC%" /Qp /DMyAppVersion=%VERSION% "%ROOT%\installer\PelicanWorkbench.iss" || goto :fail

if not exist "%RELEASE%\PelicanWorkbench_Setup_%VERSION%.exe" goto :fail

echo [6/8] Optional signing of installer...
if defined SIGNTOOL if defined PFX_PATH if defined PFX_PASSWORD (
  if defined TIMESTAMP_URL (
    "%SIGNTOOL%" sign /fd SHA256 /f "%PFX_PATH%" /p "%PFX_PASSWORD%" /tr "%TIMESTAMP_URL%" /td SHA256 "%RELEASE%\PelicanWorkbench_Setup_%VERSION%.exe" || goto :fail
  ) else (
    "%SIGNTOOL%" sign /fd SHA256 /f "%PFX_PATH%" /p "%PFX_PASSWORD%" "%RELEASE%\PelicanWorkbench_Setup_%VERSION%.exe" || goto :fail
  )
)

echo [7/8] Writing release notes...
> "%RELEASE%\BUILD_INFO.txt" echo Pelican Workbench %VERSION%
>>"%RELEASE%\BUILD_INFO.txt" echo Company/Author: TF7Z-XY
>>"%RELEASE%\BUILD_INFO.txt" echo Integrity protection: Ed25519 signed asset manifest
>>"%RELEASE%\BUILD_INFO.txt" echo Packaging: PyInstaller one-file
>>"%RELEASE%\BUILD_INFO.txt" echo Authenticode: %SIGNTOOL%

echo [8/8] Build complete.
echo.
echo ============================================================
echo  BUILD SUCCESSFUL
echo  Installer: "%RELEASE%\PelicanWorkbench_Setup_%VERSION%.exe"
echo ============================================================
start "" explorer.exe "%RELEASE%"
pause
exit /b 0

:fail
echo.
echo ============================================================
echo  BUILD FAILED
echo ============================================================
pause
exit /b 1
