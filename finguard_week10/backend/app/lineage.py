"""
Data Lineage Definition for FinGuard.

Models the flow from external sources -> raw tables -> masking ->
consumption views, plus column-level lineage for the 24 PII fields.

Returned to the frontend as a graph (nodes + edges) for react-flow / vis.
"""

from __future__ import annotations
from typing import Dict, List, Any


# -----------------------------------------------------------------------------
# Dataset-level (system) lineage
# -----------------------------------------------------------------------------
SYSTEM_NODES: List[Dict[str, Any]] = [
    # External sources
    {"id": "src_fieri",   "label": "Fieri AML",          "kind": "source",   "tier": "external"},
    {"id": "src_sec",     "label": "SEC EDGAR",          "kind": "source",   "tier": "external"},
    {"id": "src_ecb",     "label": "ECB Statistical",    "kind": "source",   "tier": "external"},
    {"id": "src_paysim",  "label": "PaySim",             "kind": "source",   "tier": "external"},
    {"id": "src_bm",      "label": "Bank Marketing",     "kind": "source",   "tier": "external"},
    {"id": "src_wb",      "label": "World Bank",         "kind": "source",   "tier": "external"},
    {"id": "src_fatf",    "label": "FATF Country Risk",  "kind": "source",   "tier": "external"},

    # Raw landing tables
    {"id": "raw_aml",     "label": "aml_transactions",        "kind": "table", "tier": "raw"},
    {"id": "raw_sec",     "label": "sec_edgar_filings",       "kind": "table", "tier": "raw"},
    {"id": "raw_ecb",     "label": "ecb_statistical_data",    "kind": "table", "tier": "raw"},
    {"id": "raw_paysim",  "label": "paysim_fraud_transactions","kind": "table","tier": "raw"},
    {"id": "raw_bm",      "label": "bank_marketing_customers","kind": "table", "tier": "raw"},
    {"id": "raw_wb",      "label": "world_bank_indicators",   "kind": "table", "tier": "raw"},
    {"id": "raw_fatf",    "label": "fatf_country_risk",       "kind": "table", "tier": "raw"},

    # Privacy layer
    {"id": "mask_engine", "label": "Masking Engine (7 methods)", "kind": "process", "tier": "privacy"},
    {"id": "vault",       "label": "Reversible Mapping Vault\n(AES-256, 28,893 entries)", "kind": "store", "tier": "privacy"},

    # Consumption views
    {"id": "view_aml",    "label": "aml_transactions_masked",        "kind": "view", "tier": "consumption"},
    {"id": "view_bm",     "label": "bank_marketing_customers_masked","kind": "view", "tier": "consumption"},
    {"id": "view_sec",    "label": "sec_edgar_filings_masked",       "kind": "view", "tier": "consumption"},
    {"id": "view_paysim", "label": "paysim_fraud_transactions_masked","kind":"view", "tier": "consumption"},

    # Consumers
    {"id": "c_aml_off",   "label": "AML Compliance Officer",   "kind": "consumer", "tier": "consumer"},
    {"id": "c_eng",       "label": "Data Engineer",            "kind": "consumer", "tier": "consumer"},
    {"id": "c_analyst",   "label": "Data Analyst",             "kind": "consumer", "tier": "consumer"},
    {"id": "c_auditor",   "label": "External Auditor (Deloitte)","kind":"consumer", "tier": "consumer"},
    {"id": "c_dpo",       "label": "DPO (full access)",        "kind": "consumer", "tier": "consumer"},
]

SYSTEM_EDGES: List[Dict[str, Any]] = [
    # source -> raw
    {"source": "src_fieri",  "target": "raw_aml",    "label": "ingest"},
    {"source": "src_sec",    "target": "raw_sec",    "label": "ingest"},
    {"source": "src_ecb",    "target": "raw_ecb",    "label": "ingest"},
    {"source": "src_paysim", "target": "raw_paysim", "label": "ingest"},
    {"source": "src_bm",     "target": "raw_bm",     "label": "ingest"},
    {"source": "src_wb",     "target": "raw_wb",     "label": "ingest"},
    {"source": "src_fatf",   "target": "raw_fatf",   "label": "ingest"},

    # raw -> masking
    {"source": "raw_aml",    "target": "mask_engine", "label": "PII fields"},
    {"source": "raw_bm",     "target": "mask_engine", "label": "PII fields"},
    {"source": "raw_sec",    "target": "mask_engine", "label": "CEO, EIN"},
    {"source": "raw_paysim", "target": "mask_engine", "label": "synthetic IDs"},

    # masking -> vault (bi-directional concept; we treat as outgoing)
    {"source": "mask_engine", "target": "vault",  "label": "stores reverse map"},

    # masking -> consumption views
    {"source": "mask_engine", "target": "view_aml",    "label": "masked"},
    {"source": "mask_engine", "target": "view_bm",     "label": "masked"},
    {"source": "mask_engine", "target": "view_sec",    "label": "masked"},
    {"source": "mask_engine", "target": "view_paysim", "label": "masked"},

    # raw -> direct (non-PII passthrough)
    {"source": "raw_ecb",  "target": "view_aml",  "label": "FX context"},
    {"source": "raw_wb",   "target": "view_aml",  "label": "country risk"},
    {"source": "raw_fatf", "target": "view_aml",  "label": "AML screening"},

    # consumption -> consumers
    {"source": "view_aml",    "target": "c_aml_off",  "label": "READ_MASKED"},
    {"source": "view_aml",    "target": "c_eng",      "label": "READ_MASKED"},
    {"source": "view_aml",    "target": "c_analyst",  "label": "READ_MASKED"},
    {"source": "view_aml",    "target": "c_auditor",  "label": "READ_ONLY masked"},
    {"source": "raw_aml",     "target": "c_dpo",      "label": "FULL access"},
    {"source": "vault",       "target": "c_dpo",      "label": "Vault unlock"},
    {"source": "view_bm",     "target": "c_analyst",  "label": "READ_MASKED"},
    {"source": "view_sec",    "target": "c_aml_off",  "label": "KYC validation"},
    {"source": "view_paysim", "target": "c_analyst",  "label": "Fraud model"},
]


# -----------------------------------------------------------------------------
# Column-level lineage for the 24 PII fields
# -----------------------------------------------------------------------------
# Each entry says: source column -> masking method -> destination column ->
# consumers that may read the destination, plus the regulatory driver.

COLUMN_LINEAGE: List[Dict[str, Any]] = [
    # ---- aml_transactions ----
    {"table": "aml_transactions", "source_column": "customer_id",        "pii_type": "Quasi",   "method": "Pseudonymization",   "dest_column": "customer_id_token",        "regulation": "GDPR Art. 4(5)", "consumers": ["AML Officer", "Data Engineer", "Data Analyst", "External Auditor"]},
    {"table": "aml_transactions", "source_column": "customer_name",      "pii_type": "Direct",  "method": "Pseudonymization",   "dest_column": "customer_name_token",      "regulation": "GDPR Art. 4(1)", "consumers": ["AML Officer", "Data Engineer"]},
    {"table": "aml_transactions", "source_column": "customer_dob",       "pii_type": "Direct",  "method": "Age-banding",        "dest_column": "customer_age_band",        "regulation": "GDPR Art. 9",    "consumers": ["AML Officer", "Data Analyst"]},
    {"table": "aml_transactions", "source_column": "customer_email",     "pii_type": "Direct",  "method": "SHA-256 Hashing",    "dest_column": "customer_email_hash",      "regulation": "GDPR Art. 4(1)", "consumers": ["Data Engineer"]},
    {"table": "aml_transactions", "source_column": "customer_phone",     "pii_type": "Direct",  "method": "Partial Masking",    "dest_column": "customer_phone_masked",    "regulation": "GLBA",           "consumers": ["AML Officer", "Data Analyst"]},
    {"table": "aml_transactions", "source_column": "customer_address",   "pii_type": "Direct",  "method": "Generalization",     "dest_column": "customer_address_city",    "regulation": "GDPR Art. 4(1)", "consumers": ["Data Analyst"]},
    {"table": "aml_transactions", "source_column": "originator_account", "pii_type": "Sensitive","method": "FPE Tokenization",  "dest_column": "originator_account_fpe",   "regulation": "PSD2",           "consumers": ["AML Officer", "Data Engineer"]},
    {"table": "aml_transactions", "source_column": "beneficiary_account","pii_type": "Sensitive","method": "FPE Tokenization",  "dest_column": "beneficiary_account_fpe",  "regulation": "PSD2",           "consumers": ["AML Officer", "Data Engineer"]},
    {"table": "aml_transactions", "source_column": "beneficiary_name",   "pii_type": "Direct",  "method": "Pseudonymization",   "dest_column": "beneficiary_name_token",   "regulation": "GDPR Art. 4(1)", "consumers": ["AML Officer"]},
    {"table": "aml_transactions", "source_column": "ip_address",         "pii_type": "Quasi",   "method": "Truncation",         "dest_column": "ip_address_trunc",         "regulation": "GDPR Recital 30","consumers": ["Data Engineer", "Data Analyst"]},
    {"table": "aml_transactions", "source_column": "device_id",          "pii_type": "Quasi",   "method": "SHA-256 Hashing",    "dest_column": "device_id_hash",           "regulation": "GDPR Art. 4(1)", "consumers": ["Data Engineer"]},

    # ---- bank_marketing_customers ----
    {"table": "bank_marketing_customers", "source_column": "customer_id",   "pii_type": "Quasi",   "method": "Pseudonymization",  "dest_column": "customer_id_token",  "regulation": "GDPR Art. 4(5)", "consumers": ["Data Analyst", "Data Engineer"]},
    {"table": "bank_marketing_customers", "source_column": "full_name",     "pii_type": "Direct",  "method": "Pseudonymization",  "dest_column": "full_name_token",    "regulation": "GDPR Art. 4(1)", "consumers": ["Data Analyst"]},
    {"table": "bank_marketing_customers", "source_column": "email",         "pii_type": "Direct",  "method": "SHA-256 Hashing",   "dest_column": "email_hash",         "regulation": "GDPR Art. 4(1)", "consumers": ["Data Engineer"]},
    {"table": "bank_marketing_customers", "source_column": "phone",         "pii_type": "Direct",  "method": "Partial Masking",   "dest_column": "phone_masked",       "regulation": "GLBA",           "consumers": ["Data Analyst"]},
    {"table": "bank_marketing_customers", "source_column": "address",       "pii_type": "Direct",  "method": "Generalization",    "dest_column": "address_city",       "regulation": "GDPR Art. 4(1)", "consumers": ["Data Analyst"]},
    {"table": "bank_marketing_customers", "source_column": "date_of_birth", "pii_type": "Direct",  "method": "Age-banding",       "dest_column": "age_band",           "regulation": "GDPR Art. 9",    "consumers": ["Data Analyst"]},
    {"table": "bank_marketing_customers", "source_column": "age",           "pii_type": "Quasi",   "method": "Age-banding",       "dest_column": "age_band",           "regulation": "EU AI Act",      "consumers": ["Data Analyst"]},
    {"table": "bank_marketing_customers", "source_column": "zip_code",      "pii_type": "Quasi",   "method": "Truncation",        "dest_column": "zip_code_trunc",     "regulation": "GDPR Art. 4(1)", "consumers": ["Data Analyst"]},

    # ---- sec_edgar_filings ----
    {"table": "sec_edgar_filings", "source_column": "ceo_name",            "pii_type": "Direct",   "method": "Pseudonymization", "dest_column": "ceo_name_token",      "regulation": "GDPR Art. 4(1)", "consumers": ["AML Officer"]},
    {"table": "sec_edgar_filings", "source_column": "headquarters_address","pii_type": "Direct",   "method": "Generalization",   "dest_column": "headquarters_city",   "regulation": "GDPR Art. 4(1)", "consumers": ["AML Officer", "Data Analyst"]},
    {"table": "sec_edgar_filings", "source_column": "ein",                 "pii_type": "Sensitive", "method": "FPE Tokenization","dest_column": "ein_fpe",             "regulation": "GLBA",           "consumers": ["AML Officer"]},

    # ---- paysim_fraud_transactions ----
    {"table": "paysim_fraud_transactions", "source_column": "name_orig",   "pii_type": "Quasi",    "method": "Pseudonymization", "dest_column": "name_orig_token", "regulation": "GDPR Art. 4(5)", "consumers": ["Data Analyst"]},
    {"table": "paysim_fraud_transactions", "source_column": "name_dest",   "pii_type": "Quasi",    "method": "Pseudonymization", "dest_column": "name_dest_token", "regulation": "GDPR Art. 4(5)", "consumers": ["Data Analyst"]},
]


def system_graph() -> Dict[str, Any]:
    """Return the dataset-level lineage graph."""
    return {"nodes": SYSTEM_NODES, "edges": SYSTEM_EDGES}


def column_graph(table: str | None = None, column: str | None = None) -> Dict[str, Any]:
    """Build a column-level mini-graph for a single column (or all)."""
    entries = COLUMN_LINEAGE
    if table:
        entries = [e for e in entries if e["table"] == table]
    if column:
        entries = [e for e in entries if e["source_column"] == column]

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def add_node(node_id: str, **kw):
        if node_id in seen:
            return
        seen.add(node_id)
        nodes.append({"id": node_id, **kw})

    for e in entries:
        src_id = f"col::{e['table']}::{e['source_column']}"
        method_id = f"method::{e['method']}::{e['table']}::{e['source_column']}"
        dest_id = f"col::{e['table']}_masked::{e['dest_column']}"

        add_node(src_id, label=e["source_column"], kind="source_column",
                 sub=f"{e['table']} ({e['pii_type']} PII)", tier="raw")
        add_node(method_id, label=e["method"], kind="process", tier="privacy",
                 sub=e["regulation"])
        add_node(dest_id, label=e["dest_column"], kind="dest_column",
                 sub=f"{e['table']}_masked", tier="consumption")
        for c in e["consumers"]:
            cid = f"consumer::{c}"
            add_node(cid, label=c, kind="consumer", tier="consumer")
            edges.append({"source": dest_id, "target": cid, "label": "READ"})
        edges.append({"source": src_id, "target": method_id, "label": "mask"})
        edges.append({"source": method_id, "target": dest_id, "label": "produces"})

    return {"nodes": nodes, "edges": edges, "rows": entries}
