"""
app/modules/auth/authentication.py — Identity Resolution.

Resolves the identity of every incoming request by checking, in order:
  1. Bearer JWT access token (Authorization: Bearer <token>)
  2. X-API-Key header
  3. Anonymous (no credentials — limited access only)

Attaches a Principal to request.state.principal on success.
Raises AuthenticationError subclasses on failure.
"""

from __future__ import annotations

from starlette.requests import Request

from app.core.logging import get_logger
from app.modules.auth.api_keys import verify_api_key
from app.modules.auth.jwt import decode_access_token
from app.modules.auth.models import Principal, PrincipalType
from app.modules.auth.permissions import get_permissions_for_roles
from app.modules.auth.store import InMemoryAuthStore
from app.api.exceptions import AuthenticationError, ApiKeyInvalidError

log = get_logger("auth.authentication")

ANONYMOUS_PRINCIPAL = Principal(
    principal_type=PrincipalType.USER,
    username="anonymous",
    roles=[],
    permissions=set(),
)


class AuthenticationService:
    """
    Resolves request identity from JWT or API key.
    In production, this would use async DB lookups via repository injection.
    """

    def __init__(self, store: InMemoryAuthStore | None = None) -> None:
        self._store = store or InMemoryAuthStore.get_instance()

    async def resolve_principal(self, request: Request) -> Principal | None:
        """
        Attempt to resolve a Principal from request headers.

        Returns:
            Principal if credentials found and valid, else None (anonymous).

        Raises:
            AuthenticationError subclass if credentials are present but invalid.
        """
        auth_header = request.headers.get("Authorization", "")
        api_key_header = request.headers.get("X-API-Key", "")

        if auth_header.startswith("Bearer "):
            return await self._resolve_jwt(auth_header[7:], request)

        if api_key_header:
            return await self._resolve_api_key(api_key_header, request)

        return None

    async def _resolve_jwt(self, token: str, request: Request) -> Principal:
        """Decode JWT and build Principal from embedded claims."""
        payload = decode_access_token(token)  # raises TokenExpiredError / TokenInvalidError
        user_id = payload.get("sub")
        roles = payload.get("roles", [])
        perms_raw = payload.get("perms", [])

        from app.modules.auth.permissions import Permission
        permissions = set()
        for p in perms_raw:
            try:
                permissions.add(Permission(p))
            except ValueError:
                pass  # Skip unknown permission codes gracefully

        principal = Principal(
            principal_type=PrincipalType.USER,
            user_id=user_id,
            roles=roles,
            permissions=permissions,
            org_id=payload.get("org_id"),
            plant_id=payload.get("plant_id"),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        log.debug(f"JWT resolved principal: user_id={user_id}, roles={roles}")
        return principal

    async def _resolve_api_key(self, raw_key: str, request: Request) -> Principal:
        """Lookup API key by hash and build Principal from stored key record."""
        import hashlib
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = self._store.get_api_key_by_hash(key_hash)

        if api_key is None or api_key.revoked:
            raise ApiKeyInvalidError()

        from datetime import datetime, timezone
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            raise ApiKeyInvalidError(message="API key has expired.")

        roles = api_key.roles
        permissions = get_permissions_for_roles(roles)

        return Principal(
            principal_type=PrincipalType.API_CLIENT,
            user_id=api_key.owner_id,
            roles=roles,
            permissions=permissions,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )


# ── Module-level singleton ─────────────────────────────────────────────────────

_auth_service: AuthenticationService | None = None


def get_auth_service() -> AuthenticationService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthenticationService()
    return _auth_service
