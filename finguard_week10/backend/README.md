# FinGuard Week 10 Backend (FastAPI)

The catalog + lineage + compliance API that powers the Week 10 web app.

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Then open <http://localhost:8000/docs> for the auto-generated Swagger UI.

By default the app reads from the project's existing files:

- Catalog metadata: `../FinGuard_Data_Catalog.xlsx`
- CSV data:         `../FinGuard_Synthetic_Datasets/`

Override either via env vars:

```bash
export FINGUARD_CATALOG=/abs/path/to/FinGuard_Data_Catalog.xlsx
export FINGUARD_DATA_DIR=/abs/path/to/FinGuard_Synthetic_Datasets
```

## Endpoints

| Endpoint                                     | Purpose                                        |
| -------------------------------------------- | ---------------------------------------------- |
| `GET  /api/health`                           | Sanity check                                   |
| `GET  /api/roles`                            | Role definitions (7 roles)                     |
| `GET  /api/catalog`                          | 98 columns, filterable                         |
| `GET  /api/catalog/summary`                  | Aggregate stats for dashboard                  |
| `GET  /api/catalog/{table}/{column}`         | Single-column detail + lineage                 |
| `GET  /api/tables/{table}/sample`            | RBAC-aware sample rows                         |
| `GET  /api/lineage/system`                   | System-level lineage graph                     |
| `GET  /api/lineage/columns`                  | Column-level lineage (filterable)              |
| `GET  /api/compliance/metrics`               | KPIs for the compliance dashboard              |
| `GET  /api/compliance/audit`                 | Recent audit log entries                       |
| `GET  /api/compliance/erasures`              | All GDPR erasure requests                      |
| `POST /api/compliance/erasure`               | Submit a new GDPR erasure (DPO/CDO only)       |

## RBAC demo

The `role` query param drives masking on the `/api/tables/.../sample` endpoint.
Try the same URL with `?role=dpo` and `?role=data_analyst` to see the
difference in real time.

| Role            | Sees raw PII | Vault access | Tables denied        |
| --------------- | :----------: | :----------: | -------------------- |
| `cdo`           | yes          | yes          | none                 |
| `dpo`           | yes          | yes          | none                 |
| `aml_officer`   | no (masked)  | no           | bank_marketing       |
| `data_engineer` | no (masked)  | no           | none                 |
| `data_analyst`  | no (masked)  | no           | none                 |
| `it_security`   | no (masked)  | yes          | none                 |
| `ext_auditor`   | no (masked)  | no           | none (read-only)     |
