# Run the FinGuard Week 10 demo on Windows

Both Python 3 and Node.js are required; you've already got both. The
scripts below do everything else.

## First time (≈ 2 minutes)

1. Open File Explorer and navigate to this folder
   (`新建文件夹\finguard_week10`).
2. Double-click **`setup.cmd`**.
   - It creates `backend\.venv`, installs FastAPI + dependencies, and runs
     `npm install` in `frontend\`.
   - You'll see a "Setup complete" message. Press any key to close.

If `setup.cmd` fails, scroll up in the window — the error message tells
you what to fix (usually a missing Python or Node, or a corporate proxy).

## Every time you want to demo

1. Double-click **`start-demo.cmd`**.
2. Two new console windows pop up — one labelled *FinGuard Backend* and
   one *FinGuard Frontend*. Leave them open.
3. Wait ~10 seconds for Vite to print
   `VITE v5.x ready in ... Local: http://localhost:5173/`.
4. In your browser, open <http://localhost:5173>.
5. The console loads with the **Data Catalog** tab and the role switcher
   set to *Data Analyst*. Follow the steps in `DEMO_RUNBOOK.md`.

To stop: close both console windows (or press `Ctrl+C` inside each).

## Running them one at a time (optional)

If you'd rather see the backend and frontend logs separately, or one of
them is misbehaving, use the standalone scripts:

- **`run-backend.cmd`** — starts only the FastAPI server on `:8000`.
- **`run-frontend.cmd`** — starts only the Vite dev server on `:5173`.

You can also run them yourself in PowerShell:

```powershell
# Terminal 1
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm run dev
```

If PowerShell blocks `Activate.ps1`, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

…or use `cmd` instead, which has no such restriction.

## Sanity checks

While the backend window is running, open
<http://localhost:8000/api/health> in your browser. You should see:

```json
{ "ok": true, "tables": [...], "catalog_columns": 98, ... }
```

If `catalog_columns` is `0`, the backend can't find
`FinGuard_Data_Catalog.xlsx`. By default it looks for the catalog and the
synthetic datasets one folder up (in `新建文件夹\`). If you've moved
those, point the backend at them by editing the top of
`run-backend.cmd`:

```cmd
set FINGUARD_CATALOG=C:\path\to\FinGuard_Data_Catalog.xlsx
set FINGUARD_DATA_DIR=C:\path\to\FinGuard_Synthetic_Datasets
```

…right before the `uvicorn` line.

## Common issues

| Symptom                                              | Fix                                                          |
| ---------------------------------------------------- | ------------------------------------------------------------ |
| `python` not found                                   | Reinstall Python and tick "Add to PATH" in the installer.    |
| `Address already in use` on 8000                     | Something else is using the port. Edit `run-backend.cmd` and change `8000` to `8001`, then update `frontend\vite.config.js` proxy target to match. |
| `Address already in use` on 5173                     | Edit `frontend\vite.config.js` to use `port: 5174`.          |
| White screen at `localhost:5173`                     | Open browser dev tools (F12) → Network — usually the backend isn't up yet. Refresh after a few seconds. |
| Vite says "failed to fetch /api/..."                 | Backend window isn't running, or it crashed. Check that window. |
| OneDrive complains the folder is busy                | Right-click the `finguard_week10` folder → *Always keep on this device*. Then re-run `setup.cmd`. |

When the demo's running you can follow `DEMO_RUNBOOK.md` for the
5-minute walkthrough.
