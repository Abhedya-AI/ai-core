"""
app/modules/auth/api_keys.py — API Key Generation and Verification.

API keys follow the format:   abhedya_<prefix>_<secret>
  prefix   : 8 hex chars — visible to the user for identification
  secret   : 32 random hex chars — full key

Storage: only the SHA-256 hash of the full key is stored.
The plaintext raw key is returned ONCE at creation time and never stored.

Verification: hash the presented key and compare to stored hash.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone


API_KEY_PREFIX_LENGTH = 8    # chars, hex
API_KEY_SECRET_LENGTH = 32   # chars, hex
API_KEY_HEADER = "X-API-Key"


@dataclass(frozen=True)
class NewApiKey:
    """Result of generate_api_key — holds both raw (once) and hash (store)."""

    raw_key: str   # abhedya_<prefix>_<secret> — return to user ONCE
    key_prefix: str  # <prefix> — stored for display
    key_hash: str    # SHA-256(raw_key) — stored in DB


def generate_api_key() -> NewApiKey:
    """
    Generate a new API key pair.

    Returns:
        NewApiKey with raw_key (shown once), key_prefix, and key_hash.
    """
    prefix = secrets.token_hex(API_KEY_PREFIX_LENGTH // 2)
    secret = secrets.token_hex(API_KEY_SECRET_LENGTH // 2)
    raw_key = f"abhedya_{prefix}_{secret}"
    key_hash = _hash_key(raw_key)
    return NewApiKey(raw_key=raw_key, key_prefix=prefix, key_hash=key_hash)


def _hash_key(raw_key: str) -> str:
    """SHA-256 hash of the raw API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(presented_key: str, stored_hash: str) -> bool:
    """
    Verify a presented API key against its stored SHA-256 hash.

    Uses hmac.compare_digest for timing-safe comparison.
    """
    import hmac
    return hmac.compare_digest(_hash_key(presented_key), stored_hash)


def extract_prefix(raw_key: str) -> str | None:
    """Extract the prefix segment from a raw API key string."""
    parts = raw_key.split("_")
    if len(parts) != 3 or parts[0] != "abhedya":
        return None
    return parts[1]
