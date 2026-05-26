@echo off
REM Starts the Vite dev server on http://localhost:5173
cd /d "%~dp0frontend"
if not exist "node_modules" (
  echo [ERROR] node_modules missing. Run setup.cmd first.
  pause
  exit /b 1
)
echo.
echo === FinGuard Frontend ===
echo  App:  http://localhost:5173
echo  Stop: Ctrl+C
echo.
call npm run dev
