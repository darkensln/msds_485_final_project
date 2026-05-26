@echo off
REM Launches backend and frontend in two new terminal windows.
setlocal
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\activate.bat" (
  echo Setup not done yet. Running setup.cmd first ...
  call setup.cmd
)

start "FinGuard Backend"  cmd /k "%~dp0run-backend.cmd"
timeout /t 4 /nobreak >nul
start "FinGuard Frontend" cmd /k "%~dp0run-frontend.cmd"

echo.
echo Two windows opened:
echo   - FinGuard Backend  : http://localhost:8000
echo   - FinGuard Frontend : http://localhost:5173
echo.
echo Wait ~10 seconds for Vite to finish booting, then open
echo     http://localhost:5173
echo in your browser.
echo.
pause
endlocal
