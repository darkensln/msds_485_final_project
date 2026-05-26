# FinGuard Week 10 Frontend (React + Vite + Tailwind)

A web console for browsing the 98-column data catalog, exploring lineage,
viewing compliance metrics, and exercising GDPR Article 17 erasure.

## Stack

- React 18, Vite, Tailwind CSS
- `reactflow` for the lineage graph
- `recharts` for dashboard charts
- Calls the FastAPI backend on `localhost:8000`

## Run locally

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`, so start
the FastAPI backend (see `../backend/README.md`) first.

To point at a different backend, set `VITE_API_BASE`:

```bash
VITE_API_BASE=http://localhost:8000/api npm run dev
```

## Views

| Tab                  | Purpose                                                      |
| -------------------- | ------------------------------------------------------------ |
| Data Catalog         | Searchable, filterable list of all 98 columns + KPIs         |
| Catalog → Detail     | Per-column metadata, DQ flags, lineage, role-aware sample    |
| Lineage              | System graph and column-level PII flow (react-flow)          |
| Compliance Dashboard | KPIs, charts, audit log, erasure history                     |
| GDPR Erasure         | Submit an Art. 17 request; cascade across tables             |

The role switcher in the header changes the active identity, which drives:

- Whether sample rows are returned masked or raw
- Whether the GDPR erasure form is enabled
- What gets logged in the audit trail
