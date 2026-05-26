"""
FinGuard Week 10 — FastAPI backend.

Endpoints:
    GET  /api/health
    GET  /api/roles
    GET  /api/catalog
    GET  /api/catalog/summary
    GET  /api/catalog/{table}/{column}
    GET  /api/tables/{table}/sample?role=...&limit=...&offset=...&search=...
    GET  /api/lineage/system
    GET  /api/lineage/columns?table=&column=
    GET  /api/compliance/metrics
    GET  /api/compliance/audit
    GET  /api/compliance/erasures
    POST /api/compliance/erasure
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import lineage as lineage_mod
from . import catalog as catalog_mod
from .store import DataStore, TABLES
from .rbac import ROLE_POLICY


# ---- Paths ----
# Allow override via env so the same image can run elsewhere.
ROOT = Path(__file__).resolve().parent.parent.parent  # finguard_week10/
DATA_DIR = Path(os.environ.get("FINGUARD_DATA_DIR",
                               ROOT.parent / "FinGuard_Synthetic_Datasets"))
CATALOG_XLSX = Path(os.environ.get("FINGUARD_CATALOG",
                                   ROOT.parent / "FinGuard_Data_Catalog.xlsx"))


# ---- App init ----
app = FastAPI(title="FinGuard Data Catalog API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Lazy globals so import errors are surfaced cleanly.
CATALOG: list[dict] = []
STORE: Optional[DataStore] = None


@app.on_event("startup")
def _startup():
    global CATALOG, STORE
    if not CATALOG_XLSX.exists():
        raise RuntimeError(f"Catalog not found: {CATALOG_XLSX}")
    CATALOG = catalog_mod.load_catalog(CATALOG_XLSX)
    STORE = DataStore(DATA_DIR, CATALOG)


# ---- Health ----
@app.get("/api/health")
def health():
    return {"ok": True, "tables": TABLES,
            "catalog_columns": len(CATALOG),
            "data_dir": str(DATA_DIR),
            "catalog_xlsx": str(CATALOG_XLSX)}


# ---- Roles ----
@app.get("/api/roles")
def roles():
    return {"roles": [{"id": r, **info} for r, info in ROLE_POLICY.items()]}


# ---- Catalog ----
@app.get("/api/catalog")
def get_catalog(
    table: Optional[str] = None,
    classification: Optional[str] = None,
    pii_only: bool = False,
    dq_issues_only: bool = False,
    search: Optional[str] = None,
):
    rows = CATALOG
    if table:
        rows = [r for r in rows if r["table"] == table]
    if classification:
        rows = [r for r in rows if r["classification"] == classification]
    if pii_only:
        rows = [r for r in rows if r["is_pii"]]
    if dq_issues_only:
        rows = [r for r in rows if r["dq_any_issue"]]
    if search:
        s = search.lower()
        rows = [r for r in rows if s in r["column"].lower()
                or s in r["table"].lower()
                or s in (r["owner"] or "").lower()
                or s in (r["steward"] or "").lower()
                or s in (r["regulation"] or "").lower()]
    return {"total": len(rows), "rows": rows}


@app.get("/api/catalog/summary")
def catalog_summary():
    return catalog_mod.summarize(CATALOG)


@app.get("/api/catalog/{table}/{column}")
def get_column_detail(table: str, column: str):
    for c in CATALOG:
        if c["table"] == table and c["column"] == column:
            # Augment with lineage if applicable
            cg = lineage_mod.column_graph(table=table, column=column)
            return {**c, "lineage": cg}
    raise HTTPException(status_code=404, detail="column not found")


# ---- Sample data (RBAC-aware) ----
@app.get("/api/tables/{table}/sample")
def sample(table: str,
           role: str = Query("data_analyst"),
           limit: int = 25,
           offset: int = 0,
           search: Optional[str] = None):
    if role not in ROLE_POLICY:
        raise HTTPException(status_code=400, detail=f"unknown role {role}")
    assert STORE is not None
    try:
        return STORE.sample(table, role, limit=limit, offset=offset, search=search)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---- Lineage ----
@app.get("/api/lineage/system")
def lineage_system():
    return lineage_mod.system_graph()


@app.get("/api/lineage/columns")
def lineage_columns(table: Optional[str] = None, column: Optional[str] = None):
    return lineage_mod.column_graph(table=table, column=column)


# ---- Compliance dashboard ----
@app.get("/api/compliance/metrics")
def compliance_metrics():
    assert STORE is not None
    summary = catalog_mod.summarize(CATALOG)
    return {
        "pii_columns": summary["pii_columns"],
        "pii_masked_columns": summary["pii_masked_columns"],
        "vault_entries": 28893,
        "erasures_processed": len(STORE.erasures()),
        "audit_log_entries": len(STORE.audit_log(limit=100000)),
        "access_denials_30d": STORE.access_denials_recent(30),
        "tables_governed": summary["total_tables"],
        "columns_governed": summary["total_columns"],
        "dq_columns_with_issue": summary["dq_columns_with_issue"],
        "by_classification": summary["by_classification"],
        "by_pii_type": summary["by_pii_type"],
        # Hard-coded operational metrics from the project narrative
        "active_sars": 12,
        "quality_gate_pass_rate": 0.962,
        "regulators_satisfied": ["GDPR", "GLBA", "PSD2", "EU AI Act", "CCPA", "EU AMLD"],
    }


@app.get("/api/compliance/audit")
def compliance_audit(limit: int = 100):
    assert STORE is not None
    return {"entries": STORE.audit_log(limit=limit)}


@app.get("/api/compliance/erasures")
def compliance_erasures():
    assert STORE is not None
    return {"erasures": STORE.erasures()}


class ErasureRequest(BaseModel):
    customer_id: str
    role: str = "dpo"
    reason: str | None = None


@app.post("/api/compliance/erasure")
def submit_erasure(req: ErasureRequest):
    if req.role not in ROLE_POLICY:
        raise HTTPException(status_code=400, detail=f"unknown role {req.role}")
    assert STORE is not None
    result = STORE.erasure_request(req.role, req.customer_id, req.reason or "")
    if not result.get("ok"):
        raise HTTPException(status_code=403, detail=result.get("error"))
    return result
