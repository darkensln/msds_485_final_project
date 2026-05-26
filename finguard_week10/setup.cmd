@echo off
REM === FinGuard Week 10 -- first-time setup ===
REM Creates a Python venv, installs FastAPI + deps, runs npm install.
REM Safe to re-run any time.

setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo  FinGuard Week 10 setup
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python is not on PATH. Install Python 3.9+ and reopen this window.
  pause
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js is not on PATH. Install Node 18+ and reopen this window.
  pause
  exit /b 1
)

echo [1/3] Creating Python virtualenv in backend\.venv ...
cd backend
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Could not create venv. Check that 'python -m venv' works.
  pause
  exit /b 1
)

echo [2/3] Installing FastAPI + dependencies ...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed.
  pause
  exit /b 1
)
call deactivate

cd ..\frontend

echo [3/3] Installing Node packages (may take 1-2 minutes) ...
if exist node_modules\ rmdir /s /q node_modules 2>nul
call npm install --no-audit --no-fund
if errorlevel 1 (
  echo [ERROR] npm install failed. See messages above.
  pause
  exit /b 1
)

cd ..

echo.
echo ============================================================
echo  Setup complete.  Next: double-click  start-demo.cmd
echo ============================================================
pause
endlocal
