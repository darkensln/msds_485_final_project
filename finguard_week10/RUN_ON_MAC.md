# Run the FinGuard Week 10 demo on **Mac (or Linux)**

Both Python 3 and Node.js are required. The scripts below do everything else.

## Prerequisites (one time)

If you don't already have them:

```bash
# Install Homebrew if needed: https://brew.sh
brew install python node
```

Verify:

```bash
python3 --version    # need 3.9+
node --version       # need 18+
```

## First time (≈ 2 minutes)

1. Open **Terminal**.
2. `cd` into this folder (`finguard_week10/`).
3. Make the scripts executable (one-time):
   ```bash
   chmod +x setup.sh run-backend.sh run-frontend.sh start-demo.sh
   ```
4. Run setup:
   ```bash
   ./setup.sh
   ```
   It creates `backend/.venv`, installs FastAPI + dependencies, and runs
   `npm install` in `frontend/`. You'll see "Setup complete" at the end.

If `setup.sh` fails, scroll up — the error message tells you what to fix
(usually a missing `python3` or `node`).

## Every time you want to demo

```bash
./start-demo.sh
```

Two new Terminal windows pop up — *FinGuard Backend* on `:8000` and
*FinGuard Frontend* on `:5173`. Leave them open. Wait ~10 seconds for
Vite to print `VITE v5.x ready in ... Local: http://localhost:5173/`,
then open <http://localhost:5173> in your browser.

The console loads with the **Data Catalog** tab and the role switcher
set to *Data Analyst*. Follow the steps in `DEMO_RUNBOOK.md`.

To stop: press `Ctrl+C` in each Terminal window, then close them.

## Running backend / frontend separately (optional)

If you'd rather see the logs in two terminals you control:

```bash
# Terminal 1
./run-backend.sh

# Terminal 2 (in a different tab/window)
./run-frontend.sh
```

Or do it manually:

```bash
# Terminal 1
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm run dev
```

## Sanity check

While the backend is running, open <http://localhost:8000/api/health>.
You should see:

```json
{ "ok": true, "tables": [...], "catalog_columns": 98, ... }
```

If `catalog_columns` is `0`, the backend can't find
`FinGuard_Data_Catalog.xlsx`. The `run-backend.sh` script sets
`FINGUARD_CATALOG` and `FINGUARD_DATA_DIR` to the `data/` folder under
this directory — if you've moved those files, edit the `export` lines in
`run-backend.sh`.

## Common issues

| Symptom | Fix |
|---|---|
| `permission denied: ./setup.sh` | Run `chmod +x setup.sh run-backend.sh run-frontend.sh start-demo.sh` |
| `python3: command not found` | `brew install python` (Mac) or install from python.org |
| `node: command not found` | `brew install node` (Mac) or install from nodejs.org |
| `Address already in use` on 8000 | Something else is using the port. Edit `run-backend.sh` and change `8000` to `8001`, then edit `frontend/vite.config.js` proxy target to match. |
| `Address already in use` on 5173 | Edit `frontend/vite.config.js` to use `port: 5174`. |
| White screen at localhost:5173 | Open dev tools (Cmd+Opt+I) → Network — usually the backend isn't up yet. Refresh after a few seconds. |
| Vite says "failed to fetch /api/..." | Backend window isn't running, or it crashed. Check that window. |
| `osascript: command not found` (Linux) | Normal — `start-demo.sh` falls back to background processes on Linux. |
| Apple Silicon: `pip install` fails on some package | Try `brew install python@3.11` and re-run setup, or upgrade pip: `pip install --upgrade pip` inside the venv. |

When the demo's running, follow `DEMO_RUNBOOK.md` for the 5-minute walkthrough.
