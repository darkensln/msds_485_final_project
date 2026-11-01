"""
RBAC enforcement layer used by the catalog API for role-aware sample data.

Roles match Section 7 of the project handover:

    cdo, dpo, aml_officer, data_engineer, data_analyst, it_security, ext_auditor
"""

from __future__ import annotations
import hashlib
import re
from typing import Any, Dict, List, Optional

# AES-256-GCM mapping vault — real reversible encryption.
# (Was previously SHA-256 only, which is irreversible. See vault.py.)
try:
    from .vault import Vault, VaultError
    _vault: Optional[Vault] = Vault.from_env()
except Exception as _e:                                # pragma: no cover
    # Cryptography library missing or key invalid — fall back to legacy hash
    # so the app still boots, but log a clear warning.
    import warnings
    warnings.warn(f"Vault disabled, falling back to SHA-256 pseudonymization: {_e}",
                  RuntimeWarning)
    _vault = None


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
    """Pseudonymize a value via the AES-256-GCM vault.

    Same value always produces the same token (deterministic), so joins
    across tables continue to work. The original value is recoverable only
    by the DPO or CDO through `vault_detokenize_for_role()`.

    Falls back to a SHA-256 hash if the vault is unavailable (preserves the
    previous behaviour so the app keeps running even without `cryptography`).
    """
    if _vault is not None:
        try:
            token = _vault.tokenize(str(v))      # 'VLT_8fae31c2b41a...'
            short = token.removeprefix("VLT_")[:8].upper()
            return f"{prefix}_{short}"
        except Exception:
            pass
    # Legacy fallback — irreversible.
    h = hashlib.sha256(str(v).encode()).hexdigest()[:6].upper()
    return f"{prefix}_{h}"


def vault_detokenize_for_role(token_or_value: str, role: str) -> Optional[str]:
    """API-layer helper: reverse a vault token, enforcing role policy.

    The vault itself enforces `role in {'cdo','dpo'}`. We accept either
    a raw 'VLT_...' token, or one of our prefixed forms like 'NAME_8FAE31C2'.
    Returns None if the token cannot be reversed (unknown, erased, or
    vault disabled).
    """
    if _vault is None:
        return None
    # Strip any '<prefix>_' so we get back the raw VLT_ token.
    if "_" in token_or_value and not token_or_value.startswith("VLT_"):
        short = token_or_value.split("_", 1)[1].lower()
        # We stored a deterministic 8-byte hex digest. Search the vault.
        for candidate, _blob in _vault._store.items():        # type: ignore[attr-defined]
            if candidate.removeprefix("VLT_").startswith(short):
                return _vault.detokenize(candidate, role=role)
        return None
    return _vault.detokenize(token_or_value, role=role)


def vault_erase(value: str) -> int:
    """GDPR Art. 17 — cryptographically erase a value from the vault.
    Returns 1 if removed, 0 if not present or vault disabled.
    """
    if _vault is None:
        return 0
    return _vault.erase(str(value))


def vault_stats() -> Dict[str, Any]:
    """Return vault telemetry for the compliance dashboard."""
    if _vault is None:
        return {"enabled": False, "entries": 0, "algorithm": "n/a"}
    s = _vault.stats()
    return {"enabled": True, "entries": s["entries"],
            "key_bits": s["key_bits"], "algorithm": "AES-256-GCM"}


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
