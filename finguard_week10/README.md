# FinGuard — Week 10 Final Deliverables

The final-week console for the FinGuard Borderless Banking project: a
searchable Data Catalog, Lineage graph, Compliance Dashboard, and GDPR
Article 17 erasure workflow, plus a full project recap deck.

## What's in this folder

```
finguard_week10/
├── README.md                ← you are here
├── DEMO_RUNBOOK.md          ← 5-minute live-demo script
├── FinGuard_Week10_Final.pptx   ← full project recap deck (18 slides)
├── backend/
│   ├── app/
│   │   ├── main.py          ← FastAPI app (12 endpoints)
│   │   ├── catalog.py       ← reads FinGuard_Data_Catalog.xlsx
│   │   ├── lineage.py       ← system + column-level lineage graph
│   │   ├── rbac.py          ← 7-role masking engine
│   │   └── store.py         ← CSV data layer + audit log + erasure cascade
│   ├── requirements.txt
│   └── README.md
└── frontend/
    ├── src/
    │   ├── App.jsx          ← shell + role switcher + tab router
    │   ├── api.js           ← thin fetch wrapper
    │   └── components/
    │       ├── CatalogView.jsx       ← Deliverable B: searchable catalog
    │       ├── ColumnDetail.jsx      ← per-column drill-in (lineage + sample)
    │       ├── LineageView.jsx       ← Deliverable A: react-flow graph
    │       ├── DashboardView.jsx     ← Deliverable C: KPIs, charts, logs
    │       └── ErasureView.jsx       ← Deliverable D: GDPR Art. 17
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── README.md
```

## The four Week 10 deliverables

| Deliverable               | Where to find it                                            |
| ------------------------- | ----------------------------------------------------------- |
| **A — Data Lineage**      | Frontend "Lineage" tab; backend `/api/lineage/{system,columns}` |
| **B — Web Data Catalog**  | Frontend "Data Catalog" tab; backend `/api/catalog`        |
| **C — Compliance Dashboard** | Frontend "Compliance Dashboard" tab; backend `/api/compliance/*` |
| **D — Final Presentation**| `FinGuard_Week10_Final.pptx` (18 slides)                    |

The GDPR Article 17 erasure workflow lives in the "GDPR Erasure" tab and is
documented in slide 14 of the deck.

## Running the console (5 minutes)

In **terminal 1** (backend):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In **terminal 2** (frontend):

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The frontend Vite dev server proxies `/api/*`
to <http://localhost:8000>, so no extra config is needed.

If the catalog/data files live elsewhere, point the backend at them:

```bash
export FINGUARD_CATALOG=/abs/path/to/FinGuard_Data_Catalog.xlsx
export FINGUARD_DATA_DIR=/abs/path/to/FinGuard_Synthetic_Datasets
uvicorn app.main:app --reload --port 8000
```

## Sources of truth

The backend is intentionally cheap to run — it reads from the existing
project artifacts rather than requiring a running PostgreSQL:

- **`../FinGuard_Data_Catalog.xlsx`** — 98 columns × 14 catalog attributes
- **`../FinGuard_Synthetic_Datasets/*.csv`** — 7 raw tables, 33,197 rows
- **`../FinGuard_Week6_Masked_Data/`** — masked datasets + mapping vault (referenced for narrative)
- **`../FinGuard_Week7_RACI_RBAC.xlsx`** — RACI matrix + RBAC permission matrix (referenced for narrative)

The PostgreSQL schema from `../FinGuard_RBAC_PostgreSQL.sql` remains the
production blueprint; the FastAPI layer mirrors its role/permission model
so you can swap CSV reads for SQL queries without changing the API surface.

## RBAC enforcement (live)

The role switcher in the header drives masking on every sample-data call:

| Role            | Sees raw PII | Vault access | Tables denied         |
| --------------- | :----------: | :----------: | --------------------- |
| CDO             | ✔            | ✔            | none                  |
| DPO             | ✔            | ✔            | none                  |
| AML Officer     |              |              | `bank_marketing_customers` |
| Data Engineer   |              |              | none (masked)         |
| Data Analyst    |              |              | none (masked)         |
| IT Security     |              | ✔            | none (masked)         |
| External Auditor|              |              | none (read-only)      |

Every read/deny is written to the in-memory audit log and visible on the
Compliance Dashboard.

See [DEMO_RUNBOOK.md](./DEMO_RUNBOOK.md) for the live-demo script.
