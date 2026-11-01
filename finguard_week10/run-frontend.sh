#!/usr/bin/env bash
# Starts the Vite dev server on http://localhost:5173
set -e
cd "$(dirname "$0")/frontend"

if [ ! -d node_modules ]; then
  echo "[ERROR] node_modules missing. Run ./setup.sh first."
  exit 1
fi

echo
echo "=== FinGuard Frontend ==="
echo "  App:  http://localhost:5173"
echo "  Stop: Ctrl+C"
echo

npm run dev
