#!/usr/bin/env bash
# Launches backend and frontend in two new Terminal windows (macOS).
# On Linux, falls back to running in the background with logs to ./logs/.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# --- run setup if missing ---
if [ ! -f "backend/.venv/bin/activate" ]; then
  echo "Setup not done yet. Running ./setup.sh first ..."
  bash ./setup.sh
fi

OS="$(uname)"

if [ "$OS" = "Darwin" ]; then
  # ----- macOS: open two Terminal tabs -----
  echo "Opening two Terminal windows..."
  osascript <<EOF
tell application "Terminal"
    do script "cd $SCRIPT_DIR && bash ./run-backend.sh"
    delay 3
    do script "cd $SCRIPT_DIR && bash ./run-frontend.sh"
    activate
end tell
EOF
  echo
  echo "Two Terminal windows opened:"
  echo "  - FinGuard Backend  : http://localhost:8000"
  echo "  - FinGuard Frontend : http://localhost:5173"
  echo
  echo "Wait ~10 seconds for Vite to finish booting, then open"
  echo "    http://localhost:5173"
  echo "in your browser."

else
  # ----- Linux: background processes -----
  mkdir -p logs
  echo "Starting backend (logs -> logs/backend.log) ..."
  nohup bash ./run-backend.sh >logs/backend.log 2>&1 &
  BACKEND_PID=$!
  echo "  Backend PID: $BACKEND_PID"
  sleep 3
  echo "Starting frontend (logs -> logs/frontend.log) ..."
  nohup bash ./run-frontend.sh >logs/frontend.log 2>&1 &
  FRONTEND_PID=$!
  echo "  Frontend PID: $FRONTEND_PID"
  echo
  echo "Both running. Stop with:"
  echo "   kill $BACKEND_PID $FRONTEND_PID"
  echo
  echo "Logs: logs/backend.log  and  logs/frontend.log"
fi
