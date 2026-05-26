"""
Data store: loads the seven synthetic CSVs and exposes a paged, RBAC-aware
sample-data API.  Also maintains an in-memory audit log + GDPR erasure log
that the compliance dashboard reads from.
"""

from __future__ import annotations
import csv
import datetime as dt
import os
import random
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .rbac import role_can_read, mask_row, ROLE_POLICY


TABLES = [
    "aml_transactions",
    "bank_marketing_customers",
    "sec_edgar_filings",
    "paysim_fraud_transactions",
    "ecb_statistical_data",
    "world_bank_indicators",
    "fatf_country_risk",
]


class DataStore:
    def __init__(self, csv_dir: Path, catalog: List[Dict[str, Any]]):
        self.csv_dir = csv_dir
        self.catalog = catalog
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._pii_by_table = self._index_pii()
        self._audit: List[Dict[str, Any]] = []
        self._erasures: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._seed_demo_history()

    # ---------- table data ----------
    def _index_pii(self) -> Dict[str, set]:
        idx: Dict[str, set] = {}
        for c in self.catalog:
            if c["is_pii"]:
                idx.setdefault(c["table"], set()).add(c["column"])
        return idx

    def _load_table(self, table: str) -> List[Dict[str, Any]]:
        if table in self._cache:
            return self._cache[table]
        path = self.csv_dir / f"{table}.csv"
        if not path.exists():
            self._cache[table] = []
            return []
        with path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self._cache[table] = rows
        return rows

    def list_tables(self) -> List[str]:
        return list(TABLES)

    def sample(self, table: str, role: str, limit: int = 25, offset: int = 0,
               search: Optional[str] = None) -> Dict[str, Any]:
        if table not in TABLES:
            raise ValueError(f"unknown table {table}")
        if not role_can_read(role, table):
            self._log(role, "DENY", f"read sample {table}")
            return {"table": table, "denied": True, "reason":
                    f"Role '{role}' is not authorized to read {table}",
                    "rows": [], "total": 0, "columns": []}
        rows = self._load_table(table)
        if search:
            s = search.lower()
            rows = [r for r in rows if any(s in str(v).lower() for v in r.values())]
        total = len(rows)
        page = rows[offset:offset + limit]
        pii = self._pii_by_table.get(table, set())
        masked = [mask_row(r, role, table, pii) for r in page]
        cols = list(page[0].keys()) if page else (rows[0].keys() if rows else [])
        self._log(role, "READ", f"{table} ({len(masked)} rows{' filtered' if search else ''})")
        return {"table": table, "denied": False, "rows": masked,
                "columns": list(cols), "total": total,
                "limit": limit, "offset": offset,
                "pii_columns": sorted(pii),
                "masked_for_role": not ROLE_POLICY[role]["see_raw"]}

    # ---------- audit log ----------
    def _log(self, role: str, decision: str, action: str):
        with self._lock:
            self._audit.append({
                "ts": dt.datetime.utcnow().isoformat() + "Z",
                "role": role,
                "decision": decision,
                "action": action,
            })

    def audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(reversed(self._audit[-limit:]))

    def access_denials_recent(self, days: int = 30) -> int:
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=days)
        with self._lock:
            return sum(1 for e in self._audit
                       if e["decision"] == "DENY"
                       and dt.datetime.fromisoformat(e["ts"][:-1]) > cutoff)

    # ---------- GDPR erasure ----------
    def erasure_request(self, role: str, customer_id: str, reason: str
                        ) -> Dict[str, Any]:
        if role not in ("cdo", "dpo"):
            self._log(role, "DENY", f"erasure request for {customer_id}")
            return {"ok": False, "error":
                    "Only CDO/DPO may submit GDPR erasure requests."}
        # Simulate cascade across tables containing this customer.
        impacted: Dict[str, int] = {}
        for t in ("aml_transactions", "bank_marketing_customers"):
            rows = self._load_table(t)
            hits = sum(1 for r in rows if r.get("customer_id") == customer_id)
            if hits:
                impacted[t] = hits
        req = {
            "id": f"ERA-{len(self._erasures)+1:04d}",
            "ts": dt.datetime.utcnow().isoformat() + "Z",
            "customer_id": customer_id,
            "requested_by": role,
            "reason": reason or "GDPR Art. 17 — Right to Erasure",
            "tables_impacted": impacted,
            "status": "Completed (cascade + vault unmap)",
        }
        with self._lock:
            self._erasures.append(req)
        self._log(role, "ERASURE", f"GDPR Art. 17 cascade for {customer_id}")
        return {"ok": True, "request": req}

    def erasures(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(reversed(self._erasures))

    # ---------- demo seeding ----------
    def _seed_demo_history(self):
        """Backfill a few weeks of believable audit + erasure events so the
        compliance dashboard isn't empty on first load."""
        rng = random.Random(42)
        now = dt.datetime.utcnow()
        roles = list(ROLE_POLICY.keys())
        actions = [("READ", "aml_transactions"), ("READ", "bank_marketing_customers"),
                   ("READ", "sec_edgar_filings"), ("READ", "paysim_fraud_transactions"),
                   ("DENY", "bank_marketing_customers"), ("READ", "fatf_country_risk")]
        for _ in range(180):
            decision, t = rng.choice(actions)
            role = rng.choice(roles)
            if decision == "DENY":
                role = "aml_officer"  # mirrors the only deny rule we ship
            offset = rng.randint(0, 60 * 24 * 30)  # last 30 days, in minutes
            ts = now - dt.timedelta(minutes=offset)
            self._audit.append({
                "ts": ts.isoformat() + "Z",
                "role": role,
                "decision": decision,
                "action": f"{t} sample read",
            })
        # 4 sample erasures already processed
        for i, cid in enumerate(["CUST-00052", "CUST-00187", "CUST-00903", "CUST-01234"]):
            ts = now - dt.timedelta(days=rng.randint(1, 25))
            self._erasures.append({
                "id": f"ERA-{i+1:04d}",
                "ts": ts.isoformat() + "Z",
                "customer_id": cid,
                "requested_by": rng.choice(["dpo", "cdo"]),
                "reason": "GDPR Art. 17 — customer request",
                "tables_impacted": {"aml_transactions": rng.randint(1, 6),
                                     "bank_marketing_customers": rng.randint(0, 1)},
                "status": "Completed (cascade + vault unmap)",
            })
