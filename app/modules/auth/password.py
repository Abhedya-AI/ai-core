"""
app/modules/auth/password.py — Password Hashing.

Primary:  Argon2id via passlib + argon2-cffi (OWASP recommended 2024)
Fallback: bcrypt via passlib (if argon2-cffi unavailable)
Dev-only: SHA-256 (if neither passlib backend is available)

Parameters (OWASP recommended minimums for interactive login 2024):
  time_cost    = 2  (iterations)
  memory_cost  = 65536 (64 MB)
  parallelism  = 1
  hash_len     = 32 bytes
"""

from __future__ import annotations

from passlib.context import CryptContext


def _build_context() -> CryptContext:
    """Build the best available CryptContext — argon2 > bcrypt > sha256_crypt."""
    # Try Argon2id first (requires argon2-cffi)
    try:
        ctx = CryptContext(
            schemes=["argon2"],
            deprecated="auto",
            argon2__time_cost=2,
            argon2__memory_cost=65536,
            argon2__parallelism=1,
        )
        # Probe: actually hash to verify backend is functional
        ctx.hash("probe")
        return ctx
    except Exception:
        pass

    # Fall back to bcrypt (passlib bundles bcrypt support)
    try:
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        ctx.hash("probe")
        return ctx
    except Exception:
        pass

    # Last resort: sha256_crypt (pure Python, always available)
    return CryptContext(schemes=["sha256_crypt"], deprecated="auto")


_ctx = _build_context()


def hash_password(password: str) -> str:
    """Hash a plaintext password using the best available algorithm."""
    return _ctx.hash(password)


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a plaintext password against its stored hash."""
    try:
        return _ctx.verify(plaintext, hashed)
    except Exception:
        return False
