"""
RBAC enforcement layer used by the catalog API for role-aware sample data.

Roles match Section 7 of the project handover:

    cdo, dpo, aml_officer, data_engineer, data_analyst, it_security, ext_auditor
"""

from __future__ import annotations
import hashlib
import re
from typing import Any, Dict, List


# Per-role access policy.  "see_raw" means the role can see unmasked PII.
ROLE_POLICY: Dict[str, Dict[str, Any]] = {
    "cdo":            {"label": "Chief Data Officer",   "tier": "Full Access",   "see_raw": True,  "vault": True},
    "dpo":            {"label": "Data Privacy Officer", "tier": "Elevated",      "see_raw": True,  "vault": True},
    "aml_officer":    {"label": "AML Compliance Officer","tier": "Elevated",     "see_raw": False, "vault": False},
    "data_engineer":  {"label": "Data Engineer",        "tier": "Standard",      "see_raw": False, "vault": False},
    "data_analyst":   {"label": "Data Analyst",         "tier": "Standard",      "see_raw": False, "vault": False},
    "it_security":    {"label": "IT Security Admin",    "tier": "Elevated",      "see_raw": False, "vault": True},
    "ext_auditor":    {"label": "External Auditor",     "tier": "Read-Only",     "see_raw": False, "vault": False},
}

# Tables whose entire row a role cannot see (rough mirror of Week 7 perm matrix).
TABLE_DENY_BY_ROLE: Dict[str, set] = {
    "ext_auditor": set(),                       # may read all (masked)
    "data_analyst": set(),
    "data_engineer": set(),
    "aml_officer": {"bank_marketing_customers"},# marketing is out of scope
    "it_security": set(),
    "dpo": set(),
    "cdo": set(),
}


# ---- Field-level masking primitives ----
def _hash(v: str) -> str:
    return "h:" + hashlib.sha256(v.encode()).hexdigest()[:12]


def _phone_partial(v: str) -> str:
    digits = re.sub(r"\D", "", v)
    if len(digits) < 4:
        return "***"
    return "***-***-" + digits[-4:]


def _email_hash(v: str) -> str:
    return _hash(v) + "@masked"


def _address_city_only(v: str) -> str:
    # Keep only the last token (rough proxy for city/state/country)
    parts = [p.strip() for p in v.split(",") if p.strip()]
    return ", ".join(parts[-2:]) if len(parts) >= 2 else (parts[-1] if parts else "***")


def _age_band(v: Any) -> str:
    try:
        age = int(v)
        if age <= 0 or age > 120:
            return "invalid"
        lo = (age // 10) * 10
        return f"{lo}-{lo+9}"
    except Exception:
        return "***"


def _dob_band(v: Any) -> str:
    try:
        s = str(v)
        year = int(s[:4])
        decade = (year // 10) * 10
        return f"{decade}s"
    except Exception:
        return "***"


def _ip_trunc(v: str) -> str:
    parts = str(v).split(".")
    if len(parts) == 4:
        return ".".join(parts[:3]) + ".XXX"
    return "***"


def _zip_trunc(v: Any) -> str:
    s = str(v)
    return s[:3] + "XX" if len(s) >= 3 else "***"


def _fpe_token(v: str) -> str:
    h = hashlib.sha256(("fpe::" + str(v)).encode()).hexdigest()
    digits = "".join(ch for ch in h if ch.isdigit())[:len(str(v))] or "0" * len(str(v))
    return "FPE" + digits[-8:]


def _pseudo(v: Any, prefix: str = "TOKEN") -> str:
    h = hashlib.sha256(str(v).encode()).hexdigest()[:6].upper()
    return f"{prefix}_{h}"


# Map column-name -> masking function.  Anything unmapped is passed through.
MASK_RULES = {
    # aml_transactions
    "customer_id":         lambda v: _pseudo(v, "CUST"),
    "customer_name":       lambda v: _pseudo(v, "NAME"),
    "customer_dob":        _dob_band,
    "customer_email":      _email_hash,
    "customer_phone":      _phone_partial,
    "customer_address":    _address_city_only,
    "originator_account":  _fpe_token,
    "beneficiary_account": _fpe_token,
    "beneficiary_name":    lambda v: _pseudo(v, "NAME"),
    "ip_address":          _ip_trunc,
    "device_id":           _hash,
    # bank_marketing
    "full_name":           lambda v: _pseudo(v, "NAME"),
    "email":               _email_hash,
    "phone":               _phone_partial,
    "address":             _address_city_only,
    "date_of_birth":       _dob_band,
    "age":                 _age_band,
    "zip_code":            _zip_trunc,
    # sec_edgar
    "ceo_name":            lambda v: _pseudo(v, "CEO"),
    "headquarters_address":_address_city_only,
    "ein":                 _fpe_token,
    # paysim
    "name_orig":           lambda v: _pseudo(v, "ORIG"),
    "name_dest":           lambda v: _pseudo(v, "DEST"),
}


def mask_row(row: Dict[str, Any], role: str, table: str,
             pii_columns: set[str]) -> Dict[str, Any]:
    """Apply masking to a single row according to role policy."""
    policy = ROLE_POLICY[role]
    if policy["see_raw"]:
        return dict(row)
    out: Dict[str, Any] = {}
    for k, v in row.items():
        if v is None or v == "":
            out[k] = v
            continue
        if k in pii_columns and k in MASK_RULES:
            try:
                out[k] = MASK_RULES[k](v)
            except Exception:
                out[k] = "***"
        else:
            out[k] = v
    return out


def role_can_read(role: str, table: str) -> bool:
    return table not in TABLE_DENY_BY_ROLE.get(role, set())
