"""
app/modules/auth/models.py — Auth domain models.

Pure Python dataclasses and Pydantic models representing:
  - Principal (resolved identity attached to every request)
  - User, Role, Session, ApiKey (persisted identity entities)

These models are intentionally decoupled from any ORM framework.
Persistence adapters (SQLAlchemy, Tortoise-ORM) map to/from these.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.modules.auth.permissions import Permission


# ── Enums ──────────────────────────────────────────────────────────────────────

class PrincipalType(str, Enum):
    """Type of identity performing a request."""
    USER = "USER"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"
    API_CLIENT = "API_CLIENT"
    AI_AGENT = "AI_AGENT"
    SYSTEM = "SYSTEM"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"
    DEACTIVATED = "DEACTIVATED"


# ── Principal ──────────────────────────────────────────────────────────────────

class Principal(BaseModel):
    """
    Resolved identity for a single authenticated request.

    Attached to request.state.principal by AuthenticationMiddleware.
    Every route handler receives this via the `get_current_principal` dependency.
    """

    principal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    principal_type: PrincipalType
    user_id: str | None = None
    username: str | None = None
    email: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: set[Permission] = Field(default_factory=set)

    # Attribute-based context (for ABAC policies)
    org_id: str | None = None
    plant_id: str | None = None
    zone_ids: list[str] = Field(default_factory=list)
    department: str | None = None
    shift: str | None = None
    clearance_level: int = 0  # 0=none … 5=classified

    # Request context
    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None

    def has_permission(self, permission: Permission) -> bool:
        """Check if this principal has a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, *permissions: Permission) -> bool:
        """Check if principal has at least one of the given permissions."""
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, *permissions: Permission) -> bool:
        """Check if principal has all of the given permissions."""
        return all(p in self.permissions for p in permissions)

    def is_in_zone(self, zone_id: str) -> bool:
        """Check if principal has access to the given zone."""
        return not self.zone_ids or zone_id in self.zone_ids


# ── User ───────────────────────────────────────────────────────────────────────

class User(BaseModel):
    """Persisted user entity."""

    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    hashed_password: str

    roles: list[str] = Field(default_factory=list)
    org_id: str | None = None
    plant_id: str | None = None
    zone_ids: list[str] = Field(default_factory=list)
    department: str | None = None
    shift: str | None = None
    clearance_level: int = 0

    status: UserStatus = UserStatus.ACTIVE
    mfa_enabled: bool = False
    mfa_secret: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Session ────────────────────────────────────────────────────────────────────

class Session(BaseModel):
    """Active user session tracked server-side for revocation support."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    refresh_token_hash: str  # SHA-256 hash of the refresh token
    ip_address: str | None = None
    user_agent: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    last_used_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked: bool = False
    revoked_at: datetime | None = None


# ── API Key ────────────────────────────────────────────────────────────────────

class ApiKey(BaseModel):
    """Service / integration API key."""

    key_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key_prefix: str  # First 8 chars of raw key (shown to user for identification)
    key_hash: str   # SHA-256 hash of full key (stored, never plaintext)
    name: str       # Human label e.g. "SCADA Integration", "Monitoring Bot"
    owner_id: str   # User ID or service account ID
    roles: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    revoked: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Audit Log Entry ────────────────────────────────────────────────────────────

class AuthAuditEntry(BaseModel):
    """Immutable record of a privileged auth action."""

    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    actor_id: str
    actor_type: PrincipalType
    action: str   # e.g. "LOGIN_SUCCESS", "TOKEN_REFRESH", "PERMISSION_DENIED"
    resource: str | None = None
    result: str   # "SUCCESS" | "FAILURE"

    ip_address: str | None = None
    user_agent: str | None = None
    trace_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
