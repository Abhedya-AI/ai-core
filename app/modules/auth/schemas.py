"""
app/modules/auth/schemas.py — Auth API request/response schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


# ── Login ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Credentials for username/password login."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """JWT token pair returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900  # seconds (15 minutes)


class RefreshRequest(BaseModel):
    """Refresh token for rotating the access token."""

    refresh_token: str


# ── User ───────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Public user information returned by /auth/me."""

    user_id: str
    username: str
    email: str
    full_name: str
    roles: list[str]
    permissions: list[str]
    org_id: str | None
    plant_id: str | None
    department: str | None
    shift: str | None


class CreateUserRequest(BaseModel):
    """Admin: create a new user."""

    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(...)
    full_name: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=10, max_length=128)
    roles: list[str] = Field(default_factory=list)
    plant_id: str | None = None
    department: str | None = None
    shift: str | None = None


class UpdateRolesRequest(BaseModel):
    """Admin: update roles for a user."""

    roles: list[str]


# ── API Keys ───────────────────────────────────────────────────────────────────

class CreateApiKeyRequest(BaseModel):
    """Create a new API key."""

    name: str = Field(..., min_length=3, max_length=128)
    roles: list[str] = Field(default_factory=list)
    expires_days: int | None = Field(default=365, ge=1, le=3650)


class ApiKeyResponse(BaseModel):
    """API key creation response — raw_key shown ONCE."""

    key_id: str
    key_prefix: str
    name: str
    roles: list[str]
    raw_key: str | None = None  # Only included at creation time
    expires_at: str | None = None
