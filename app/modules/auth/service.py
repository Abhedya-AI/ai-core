"""
app/modules/auth/service.py — Auth Application Service.

Orchestrates login, token refresh, logout, user management, and API key management.
Sits between the HTTP routes and the underlying store/JWT/password modules.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from app.core.logging import get_logger
from app.api.exceptions import AuthenticationError, NotFoundError, ConflictError
from app.modules.auth.api_keys import generate_api_key
from app.modules.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.modules.auth.models import ApiKey, AuthAuditEntry, PrincipalType, Session, User
from app.modules.auth.password import hash_password, verify_password
from app.modules.auth.permissions import get_permissions_for_roles
from app.modules.auth.schemas import (
    ApiKeyResponse,
    CreateApiKeyRequest,
    CreateUserRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.store import InMemoryAuthStore

log = get_logger("auth.service")


class AuthService:
    """Handles authentication, session management, user and API key operations."""

    def __init__(self, store: InMemoryAuthStore | None = None) -> None:
        self._store = store or InMemoryAuthStore.get_instance()

    # ── Login / Refresh / Logout ───────────────────────────────────────────────

    async def login(self, request: LoginRequest, ip: str | None = None, ua: str | None = None) -> TokenResponse:
        """Authenticate user credentials and issue a JWT token pair."""
        user = self._store.get_user_by_username(request.username)

        if not user or not verify_password(request.password, user.hashed_password):
            self._audit("unknown", PrincipalType.USER, "LOGIN_FAILURE", result="FAILURE", ip=ip)
            raise AuthenticationError(message="Invalid username or password.")

        if user.status.value != "ACTIVE":
            raise AuthenticationError(message=f"Account is {user.status.value.lower()}.")

        # Create session + refresh token
        session = Session(
            user_id=user.user_id,
            refresh_token_hash="",  # set below after creating refresh token
            ip_address=ip,
            user_agent=ua,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        refresh_token = create_refresh_token(user.user_id, session.session_id)
        session = session.model_copy(
            update={"refresh_token_hash": hashlib.sha256(refresh_token.encode()).hexdigest()}
        )
        self._store.save_session(session)

        perms = get_permissions_for_roles(user.roles)
        access_token = create_access_token(
            user_id=user.user_id,
            roles=user.roles,
            permissions=[p.value for p in perms],
            org_id=user.org_id,
            plant_id=user.plant_id,
        )

        self._audit(user.user_id, PrincipalType.USER, "LOGIN_SUCCESS", result="SUCCESS", ip=ip)
        log.info(f"User '{user.username}' logged in successfully.")
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Rotate the access token using a valid refresh token (one-time-use)."""
        from app.api.exceptions import TokenInvalidError
        payload = decode_refresh_token(refresh_token)

        session_id = payload.get("sid")
        user_id = payload.get("sub")
        session = self._store.get_session(session_id)

        if session is None or session.revoked:
            raise TokenInvalidError(message="Session has been revoked or does not exist.")

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if token_hash != session.refresh_token_hash:
            raise TokenInvalidError(message="Refresh token does not match session.")

        user = self._store.get_user_by_id(user_id)
        if not user:
            raise TokenInvalidError(message="User no longer exists.")

        # Revoke old session, create new one (refresh token rotation)
        self._store.revoke_session(session_id)
        new_session = Session(
            user_id=user.user_id,
            refresh_token_hash="",
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        new_refresh = create_refresh_token(user.user_id, new_session.session_id)
        new_session = new_session.model_copy(
            update={"refresh_token_hash": hashlib.sha256(new_refresh.encode()).hexdigest()}
        )
        self._store.save_session(new_session)

        perms = get_permissions_for_roles(user.roles)
        access_token = create_access_token(
            user_id=user.user_id,
            roles=user.roles,
            permissions=[p.value for p in perms],
            org_id=user.org_id,
            plant_id=user.plant_id,
        )
        return TokenResponse(access_token=access_token, refresh_token=new_refresh)

    async def logout(self, session_id: str, user_id: str) -> None:
        """Revoke the current session (single device logout)."""
        self._store.revoke_session(session_id)
        self._audit(user_id, PrincipalType.USER, "LOGOUT", result="SUCCESS")

    async def logout_all(self, user_id: str) -> int:
        """Revoke all sessions for the user (all devices logout)."""
        count = self._store.revoke_all_sessions(user_id)
        self._audit(user_id, PrincipalType.USER, "LOGOUT_ALL", result="SUCCESS")
        return count

    # ── User Info ──────────────────────────────────────────────────────────────

    async def get_me(self, user_id: str) -> UserResponse:
        """Get the current user's profile."""
        user = self._store.get_user_by_id(user_id)
        if not user:
            raise NotFoundError(message="User not found.")
        perms = get_permissions_for_roles(user.roles)
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            permissions=[p.value for p in perms],
            org_id=user.org_id,
            plant_id=user.plant_id,
            department=user.department,
            shift=user.shift,
        )

    # ── User Management (Admin) ────────────────────────────────────────────────

    async def create_user(self, request: CreateUserRequest) -> UserResponse:
        """Create a new user (admin only)."""
        if self._store.get_user_by_username(request.username):
            raise ConflictError(message=f"Username '{request.username}' is already taken.")

        user = User(
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            hashed_password=hash_password(request.password),
            roles=request.roles,
            plant_id=request.plant_id,
            department=request.department,
            shift=request.shift,
            org_id="ORG-001",
        )
        self._store.save_user(user)
        log.info(f"Admin created user '{user.username}' with roles {user.roles}")
        perms = get_permissions_for_roles(user.roles)
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
            permissions=[p.value for p in perms],
            org_id=user.org_id,
            plant_id=user.plant_id,
            department=user.department,
            shift=user.shift,
        )

    async def list_users(self) -> list[UserResponse]:
        users = self._store.list_users()
        result = []
        for u in users:
            perms = get_permissions_for_roles(u.roles)
            result.append(UserResponse(
                user_id=u.user_id,
                username=u.username,
                email=u.email,
                full_name=u.full_name,
                roles=u.roles,
                permissions=[p.value for p in perms],
                org_id=u.org_id,
                plant_id=u.plant_id,
                department=u.department,
                shift=u.shift,
            ))
        return result

    # ── API Key Management ─────────────────────────────────────────────────────

    async def create_api_key(self, request: CreateApiKeyRequest, owner_id: str) -> ApiKeyResponse:
        """Generate a new API key."""
        new_key = generate_api_key()
        expires_at = None
        if request.expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_days)

        api_key = ApiKey(
            key_prefix=new_key.key_prefix,
            key_hash=new_key.key_hash,
            name=request.name,
            owner_id=owner_id,
            roles=request.roles,
            expires_at=expires_at,
        )
        self._store.save_api_key(api_key)
        log.info(f"API key '{request.name}' created for owner {owner_id}")
        return ApiKeyResponse(
            key_id=api_key.key_id,
            key_prefix=api_key.key_prefix,
            name=api_key.name,
            roles=api_key.roles,
            raw_key=new_key.raw_key,  # Shown once
            expires_at=expires_at.isoformat() if expires_at else None,
        )

    # ── Audit ──────────────────────────────────────────────────────────────────

    def _audit(
        self,
        actor_id: str,
        actor_type: PrincipalType,
        action: str,
        result: str,
        ip: str | None = None,
    ) -> None:
        entry = AuthAuditEntry(
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            result=result,
            ip_address=ip,
        )
        self._store.save_audit_entry(entry)


# ── Module singleton ───────────────────────────────────────────────────────────

_auth_svc: AuthService | None = None


def get_auth_service_instance() -> AuthService:
    global _auth_svc
    if _auth_svc is None:
        _auth_svc = AuthService()
    return _auth_svc
