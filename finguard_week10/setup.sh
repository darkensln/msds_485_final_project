#!/usr/bin/env bash
# === FinGuard Week 10 — first-time setup (Mac / Linux) ===
# Creates a Python venv, installs FastAPI + deps, runs npm install.
# Safe to re-run any time.

set -e
cd "$(dirname "$0")"

echo
echo "============================================================"
echo "  FinGuard Week 10 setup (Mac/Linux)"
echo "============================================================"
echo

# --- Check prerequisites ---
if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 is not on PATH."
  echo "        Install from https://www.python.org/downloads/ (3.9+ required)"
  echo "        or 'brew install python' if you have Homebrew."
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "[ERROR] node is not on PATH."
  echo "        Install from https://nodejs.org/ (18+ required)"
  echo "        or 'brew install node' if you have Homebrew."
  exit 1
fi

PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
NODE_VER=$(node --version 2>&1)
echo "Found: Python $PY_VER, Node $NODE_VER"
echo

# --- Step 1: backend venv ---
echo "[1/3] Creating Python virtualenv in backend/.venv ..."
cd backend
if [ ! -f ".venv/bin/python" ]; then
  python3 -m venv .venv
fi
if [ ! -f ".venv/bin/python" ]; then
  echo "[ERROR] Could not create venv. Check that 'python3 -m venv' works."
  exit 1
fi

# --- Step 2: install Python deps ---
echo "[2/3] Installing FastAPI + dependencies ..."
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
deactivate

# --- Step 3: install Node deps ---
cd ../frontend
echo "[3/3] Installing Node packages (may take 1-2 minutes) ..."
if [ -d node_modules ]; then
  rm -rf node_modules
fi
npm install --no-audit --no-fund

cd ..
echo
echo "============================================================"
echo "  Setup complete.  Next: ./start-demo.sh"
echo "============================================================"
