"""
Vault: real reversible encryption for the FinGuard mapping vault.

Until now the project narrative claimed AES-256 encryption but the actual
code used SHA-256 (one-way hashes) for tokenization. This module fixes
that gap by implementing AES-256-GCM authenticated encryption — the same
algorithm used in TLS 1.3, signal protocol, and most modern KMS systems.

References:
    - NIST SP 800-38D (GCM mode)
    - GDPR Art. 32(1)(a) — encryption of personal data
    - GLBA Safeguards Rule 16 CFR § 314.4(c)(8) — encryption at rest

USAGE
-----
    from app.vault import Vault

    vault = Vault.from_env()        # picks up FINGUARD_VAULT_KEY
    token = vault.tokenize("Donato Godoy-Chaparro")
    # → 'VLT_8fae31...c2b4'

    original = vault.detokenize(token, role="dpo")
    # → 'Donato Godoy-Chaparro'
    # Raises PermissionError for any role other than dpo/cdo.

    vault.erase("Donato Godoy-Chaparro")
    # GDPR Art. 17 — removes from the vault so the token can no longer be
    # reversed. The token still appears in masked tables but maps to nothing.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from pathlib import Path
from typing import Dict, Optional

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _HAS_CRYPTO = True
except ImportError:                                                # pragma: no cover
    _HAS_CRYPTO = False


# Roles authorised to reverse a token. Mirrors ROLE_POLICY in rbac.py.
_REVERSE_ALLOWED = {"cdo", "dpo"}


class VaultError(Exception):
    pass


class Vault:
    """AES-256-GCM authenticated encryption for the FinGuard mapping vault.

    The vault is the single source of truth for re-identifying a tokenised
    value. The encryption key is held outside the application (env var in
    development, KMS in production). Tokens are deterministic — the same
    plaintext always produces the same token — so joins across tables work,
    but the underlying ciphertext is non-deterministic per the GCM nonce.
    """

    KEY_BYTES = 32   # 256 bits
    NONCE_BYTES = 12 # 96 bits — NIST-recommended GCM nonce length

    def __init__(self, key: bytes, salt: bytes = b"FinGuard-v1"):
        if not _HAS_CRYPTO:
            raise VaultError(
                "The 'cryptography' package is required for Vault. "
                "Add `cryptography>=42.0` to requirements.txt and reinstall."
            )
        if len(key) != self.KEY_BYTES:
            raise VaultError(f"Vault key must be {self.KEY_BYTES} bytes, got {len(key)}")
        self._aesgcm = AESGCM(key)
        self._salt = salt
        # In-memory store: token -> ciphertext blob. In production this is
        # a database table (`raw_pii.mapping_vault` in our Postgres schema).
        self._store: Dict[str, bytes] = {}

    # ---------------------------------------------------------------- factory
    @classmethod
    def from_env(cls, env_var: str = "FINGUARD_VAULT_KEY") -> "Vault":
        """Load the AES key from an environment variable (base64-encoded).

        For local dev: set FINGUARD_VAULT_KEY to a 44-character base64 string.
        Generate one with:  python -c 'import secrets,base64;print(base64.b64encode(secrets.token_bytes(32)).decode())'

        If unset, generates an ephemeral key (warning: tokens will not
        reverse across process restarts).
        """
        raw = os.environ.get(env_var)
        if raw:
            try:
                key = base64.b64decode(raw)
            except Exception as e:
                raise VaultError(f"{env_var} is not valid base64: {e}")
        else:
            key = secrets.token_bytes(cls.KEY_BYTES)
            import warnings
            warnings.warn(
                f"{env_var} not set; using ephemeral key. Tokens will be "
                f"unreversible after restart. OK for demo, NOT for production.",
                RuntimeWarning,
            )
        return cls(key)

    # ------------------------------------------------------------ tokenize
    def tokenize(self, plaintext: str) -> str:
        """Encrypt `plaintext` and return a deterministic token.

        Same plaintext → same token (so joins still work).
        Token format: 'VLT_' + first 16 hex chars of HMAC-style derivation.
        """
        if plaintext is None or plaintext == "":
            return plaintext

        pt = str(plaintext)

        # 1. Deterministic token: SHA-256(salt || plaintext) truncated.
        digest = hashlib.sha256(self._salt + pt.encode("utf-8")).digest()
        token = "VLT_" + digest[:8].hex()

        # 2. If we've seen this plaintext before, no need to re-encrypt.
        if token in self._store:
            return token

        # 3. Encrypt with AES-256-GCM. Nonce is random and stored with the
        #    ciphertext (NIST SP 800-38D requires unique nonces per key).
        nonce = secrets.token_bytes(self.NONCE_BYTES)
        ciphertext = self._aesgcm.encrypt(nonce, pt.encode("utf-8"), associated_data=token.encode())
        self._store[token] = nonce + ciphertext  # nonce | ciphertext+tag

        return token

    # ---------------------------------------------------------- detokenize
    def detokenize(self, token: str, role: str) -> Optional[str]:
        """Reverse a token to its original plaintext.

        Only the CDO and DPO roles are allowed; everyone else gets a
        PermissionError. This is the in-process equivalent of the
        `raw_pii` schema GRANT in our Postgres RBAC.
        """
        if role not in _REVERSE_ALLOWED:
            raise PermissionError(
                f"Role '{role}' may not reverse vault tokens. "
                f"Allowed: {sorted(_REVERSE_ALLOWED)}"
            )
        blob = self._store.get(token)
        if blob is None:
            return None                          # token unknown or already erased
        nonce, ciphertext = blob[: self.NONCE_BYTES], blob[self.NONCE_BYTES :]
        try:
            pt = self._aesgcm.decrypt(nonce, ciphertext, associated_data=token.encode())
        except Exception as e:
            raise VaultError(f"Authentication failed when decrypting {token}: {e}")
        return pt.decode("utf-8")

    # ---------------------------------------------------------------- erase
    def erase(self, plaintext_or_token: str) -> int:
        """Remove an entry from the vault — GDPR Art. 17 cascade.

        Accepts either the original plaintext or its token. Returns 1 if a
        record was found and removed, 0 otherwise. After erasure the token
        still exists in masked tables but is no longer reversible — i.e.,
        the data effectively becomes anonymous per GDPR Recital 26.
        """
        if plaintext_or_token.startswith("VLT_"):
            token = plaintext_or_token
        else:
            digest = hashlib.sha256(self._salt + plaintext_or_token.encode("utf-8")).digest()
            token = "VLT_" + digest[:8].hex()
        if token in self._store:
            del self._store[token]
            return 1
        return 0

    # ----------------------------------------------------------- metadata
    def stats(self) -> Dict[str, int]:
        return {"entries": len(self._store), "key_bits": self.KEY_BYTES * 8}


# ---------------------------------------------------------------- demo / cli
if __name__ == "__main__":
    print("FinGuard Vault — AES-256-GCM demo")
    print("=" * 50)

    # Use a fixed key so the demo is reproducible.
    demo_key = hashlib.sha256(b"FinGuard-demo-key").digest()
    vault = Vault(demo_key)

    samples = [
        "Donato Godoy-Chaparro",
        "rocaamilcar@example.org",
        "GB93LLTI07816184959310",
        "Donato Godoy-Chaparro",   # duplicate to prove tokens are stable
    ]

    print("\n1. Tokenize four values (note: duplicates collapse):")
    tokens = []
    for s in samples:
        t = vault.tokenize(s)
        tokens.append(t)
        print(f"   '{s[:30]:30s}'  →  {t}")

    print(f"\n   Vault now contains {vault.stats()['entries']} unique entries.")

    print("\n2. Detokenize as DPO (allowed):")
    for t in set(tokens):
        print(f"   {t}  →  '{vault.detokenize(t, role='dpo')}'")

    print("\n3. Try to detokenize as Data Analyst (denied):")
    try:
        vault.detokenize(tokens[0], role="data_analyst")
    except PermissionError as e:
        print(f"   PermissionError: {e}")

    print("\n4. GDPR Art. 17 erasure — remove Donato:")
    removed = vault.erase("Donato Godoy-Chaparro")
    print(f"   Erased {removed} record(s). Vault now has {vault.stats()['entries']} entries.")
    result = vault.detokenize(tokens[0], role="dpo")
    print(f"   Detokenize {tokens[0]} as DPO now returns: {result!r}")
    print(f"   ← None means the token can no longer be reversed.")
    print(f"   The token remains in masked tables but maps to nothing —")
    print(f"   which is exactly what GDPR Recital 26 calls 'anonymous data'.")

    print("\nDone.")
