@echo off
REM Starts the FastAPI backend on http://localhost:8000
cd /d "%~dp0backend"
if not exist ".venv\Scripts\activate.bat" (
  echo [ERROR] Backend venv missing. Run setup.cmd first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
echo.
echo === FinGuard Backend ===
echo  Endpoints: http://localhost:8000/docs
echo  Stop:      Ctrl+C
echo.
uvicorn app.main:app --reload --port 8000
