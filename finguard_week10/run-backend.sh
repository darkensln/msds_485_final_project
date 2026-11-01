#!/usr/bin/env bash
# Starts the FastAPI backend on http://localhost:8000
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/backend"

if [ ! -f ".venv/bin/activate" ]; then
  echo "[ERROR] Backend venv missing. Run ./setup.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

export FINGUARD_CATALOG="$SCRIPT_DIR/data/FinGuard_Data_Catalog.xlsx"
export FINGUARD_DATA_DIR="$SCRIPT_DIR/data/synthetic"

echo
echo "=== FinGuard Backend ==="
echo "  Endpoints: http://localhost:8000/docs"
echo "  Health:    http://localhost:8000/api/health"
echo "  Stop:      Ctrl+C"
echo

uvicorn app.main:app --reload --reload-dir app --port 8000
