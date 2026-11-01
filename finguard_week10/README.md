# FinGuard — Week 10 Console

Searchable Data Catalog, Lineage graph, Compliance Dashboard, GDPR Article 17 erasure workflow, and a
UNESCO AI-ethics crosswalk, all gated by the role you're signed in as. Plus the Week 8 fairness notebook.

## Run it

Needs **Python 3.9+** and **Node 18+**.

**Mac / Linux**

```bash
cd finguard_week10
chmod +x *.sh        # first time only
./setup.sh           # first time only: Python venv + npm install
./start-demo.sh      # opens backend + frontend (or run ./run-backend.sh and ./run-frontend.sh in two terminals)
```

**Windows:** `setup.cmd`, then `start-demo.cmd` (details in `RUN_ON_WINDOWS.md`).

Open <http://localhost:5173>. API docs: <http://localhost:8000/docs>.

If the frontend says `vite: command not found`, the Node packages aren't installed — re-run `./setup.sh`.

Manual start (any OS):

```bash
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
uvicorn app.main:app --reload --reload-dir app --port 8000
# second terminal
cd frontend && npm install && npm run dev
```

The backend reads `data/FinGuard_Data_Catalog.xlsx` and `data/synthetic/*.csv` by default; override with
`FINGUARD_CATALOG` / `FINGUARD_DATA_DIR`.

## What's in this folder

```
finguard_week10/
├── week8_fairness_audit.ipynb   ← Week 8: four-fifths rule + significance tests (pip install -r requirements-notebook.txt)
├── DEMO_RUNBOOK.md              ← live-demo script
├── FinGuard_Week10_Final.pptx   ← final deck
├── data/                        ← catalog workbook + 7 synthetic tables (33,197 rows)
├── backend/app/
│   ├── main.py      ← FastAPI app (15 endpoints)
│   ├── catalog.py   ← reads the 98-column catalog
│   ├── lineage.py   ← system + column-level lineage graph
│   ├── rbac.py      ← 7-role masking engine
│   ├── vault.py     ← AES-256-GCM token vault (tokenize / role-gated detokenize / erase)
│   ├── ethics.py    ← UNESCO AI-ethics crosswalk (10 principles → 30 controls)
│   └── store.py     ← CSV data layer, audit log, GDPR erasure cascade
└── frontend/src/components/
    ├── CatalogView.jsx · ColumnDetail.jsx · LineageView.jsx
    ├── DashboardView.jsx · ErasureView.jsx · EthicsView.jsx
```

## Access model

| Role | Sees raw PII | Can decrypt vault tokens | Can submit GDPR erasure | Tables denied |
|---|:-:|:-:|:-:|---|
| Chief Data Officer (CDO) | ✔ | ✔ | ✔ | none |
| Data Privacy Officer (DPO) | ✔ | ✔ | ✔ | none |
| AML Compliance Officer | | | | `bank_marketing_customers` |
| Data Engineer | | | | none (masked) |
| Data Analyst | | | | none (masked) |
| IT Security Admin | | | | none (masked; administers vault keys, cannot decrypt) |
| External Auditor | | | | none (read-only, masked) |

Every read and denial is written to the audit log shown on the Compliance Dashboard.

**Masking methods:** pseudonymisation (vault-backed, reversible by DPO/CDO), SHA-256 hashing (emails,
device IDs), partial masking (phones), generalisation (addresses → city/region), decade age bands (DOB, age),
truncation (IP, ZIP), format-preserving tokens (account numbers, EINs).

## Quick proofs (curl)

```bash
# Same row, two roles
curl "localhost:8000/api/tables/aml_transactions/sample?role=data_analyst&limit=1"
curl "localhost:8000/api/tables/aml_transactions/sample?role=dpo&limit=1"

# Decrypt a token: analyst → 403, DPO → 200
curl -X POST localhost:8000/api/vault/detokenize -H 'content-type: application/json' \
     -d '{"token":"NAME_20CCDFBE","role":"data_analyst"}'

# GDPR erasure (second identical request is refused)
curl -X POST localhost:8000/api/compliance/erasure -H 'content-type: application/json' \
     -d '{"customer_id":"CUST-00099","role":"dpo"}'
```

Tokens only enter the vault when a masked role views a row, so **view a customer's rows as Data Analyst
before erasing them** if you want the erasure to report vault records removed.

## Demo-state notes

- Audit log, erasure history and vault live in memory and reset on restart. Four historical erasures and
  180 audit entries are seeded on startup.
- The vault key is ephemeral unless `FINGUARD_VAULT_KEY` is set (32-byte base64). In production it would come
  from a KMS.
- "Active SARs" and "Quality gate pass" on the dashboard are illustrative values and are labelled as such.
