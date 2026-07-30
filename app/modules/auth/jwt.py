"""
app/modules/auth/jwt.py — JWT Token Management.

Access tokens:   HS256-signed JWTs, 15-minute expiry
Refresh tokens:  HS256-signed JWTs, 7-day expiry (one-time-use via session store)

Token claims:
  sub      : user_id
  jti      : unique token ID (for revocation)
  type     : "access" | "refresh"
  roles    : list[str]
  perms    : list[str]  (permission codes)
  org_id   : str | None
  plant_id : str | None
  exp      : Unix timestamp
  iat      : Unix timestamp
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings
from app.core.logging import get_logger
from app.api.exceptions import TokenExpiredError, TokenInvalidError

log = get_logger("auth.jwt")

# Algorithm — HMAC-SHA256 (symmetric, simple for single-service deployment)
# For multi-service, swap to RS256 with asymmetric key pair.
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _secret() -> str:
    """Return the JWT signing secret from settings."""
    return settings.security.secret_key


def create_access_token(
    user_id: str,
    roles: list[str],
    permissions: list[str],
    *,
    org_id: str | None = None,
    plant_id: str | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        user_id: Subject identifier.
        roles: List of role names to embed.
        permissions: List of permission code strings.
        org_id: Organisation scope (for ABAC).
        plant_id: Plant scope (for ABAC).
        extra_claims: Additional claims merged into payload.

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "type": "access",
        "roles": roles,
        "perms": permissions,
        "org_id": org_id,
        "plant_id": plant_id,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def create_refresh_token(user_id: str, session_id: str) -> str:
    """
    Create a long-lived refresh token tied to a session.

    Args:
        user_id: Subject identifier.
        session_id: Server-side session ID for revocation tracking.

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "sid": session_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Raises:
        TokenExpiredError: if token has expired.
        TokenInvalidError: if signature or structure is invalid.

    Returns:
        Decoded payload dict.
    """
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise TokenInvalidError(message="Token type mismatch — expected 'access'.")
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.PyJWTError as exc:
        raise TokenInvalidError(message=f"Token validation failed: {exc}")


def decode_refresh_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT refresh token.

    Raises:
        TokenExpiredError, TokenInvalidError.

    Returns:
        Decoded payload dict including `sid` (session_id).
    """
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise TokenInvalidError(message="Token type mismatch — expected 'refresh'.")
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError(message="Refresh token has expired. Please log in again.")
    except jwt.PyJWTError as exc:
        raise TokenInvalidError(message=f"Refresh token validation failed: {exc}")
