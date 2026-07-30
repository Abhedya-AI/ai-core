"""
tests/test_auth.py — Authentication & Authorization Test Suite.

Covers:
  - Password hashing/verification
  - JWT token creation, decoding, and expiry
  - API key generation and verification
  - Login success / failure
  - Token refresh rotation
  - Permission resolution (RBAC)
  - Principal permission checking
  - Auth dependency enforcement
"""

import pytest

from app.modules.auth.api_keys import generate_api_key, verify_api_key, extract_prefix
from app.modules.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.modules.auth.password import hash_password, verify_password
from app.modules.auth.permissions import Permission, get_permissions_for_roles
from app.modules.auth.models import Principal, PrincipalType
from app.modules.auth.schemas import LoginRequest, CreateApiKeyRequest
from app.modules.auth.service import AuthService
from app.modules.auth.store import InMemoryAuthStore
from app.api.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    TokenInvalidError,
    PermissionDeniedError,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def store():
    """Fresh auth store for each test."""
    s = InMemoryAuthStore()
    return s


@pytest.fixture
def auth_service(store):
    return AuthService(store=store)


# ── Password ───────────────────────────────────────────────────────────────────

def test_password_hash_and_verify():
    """Hashing a password and verifying it works correctly."""
    password = "SecureP@ssw0rd!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_password_wrong_password_fails():
    """Wrong password does not verify."""
    hashed = hash_password("CorrectPassword123!")
    assert not verify_password("WrongPassword!", hashed)


def test_password_empty_string_does_not_verify():
    """Empty password does not match hashed non-empty password."""
    hashed = hash_password("somepassword")
    assert not verify_password("", hashed)


# ── JWT ────────────────────────────────────────────────────────────────────────

def test_create_and_decode_access_token():
    """Access token can be created and decoded correctly."""
    token = create_access_token(
        user_id="U-001",
        roles=["SAFETY_OFFICER"],
        permissions=["risk.run", "incident.read"],
        org_id="ORG-001",
        plant_id="PLANT-001",
    )
    payload = decode_access_token(token)
    assert payload["sub"] == "U-001"
    assert payload["type"] == "access"
    assert "risk.run" in payload["perms"]
    assert payload["org_id"] == "ORG-001"


def test_create_and_decode_refresh_token():
    """Refresh token encodes user_id and session_id."""
    token = create_refresh_token(user_id="U-002", session_id="SID-001")
    payload = decode_refresh_token(token)
    assert payload["sub"] == "U-002"
    assert payload["sid"] == "SID-001"
    assert payload["type"] == "refresh"


def test_decode_invalid_jwt_raises_token_invalid_error():
    """Tampered JWT raises TokenInvalidError."""
    with pytest.raises(TokenInvalidError):
        decode_access_token("not.a.real.jwt")


def test_decode_wrong_type_raises_token_invalid_error():
    """Passing a refresh token to decode_access_token raises TokenInvalidError."""
    refresh_token = create_refresh_token(user_id="U-001", session_id="SID-001")
    with pytest.raises(TokenInvalidError):
        decode_access_token(refresh_token)


def test_decode_wrong_refresh_type_raises_token_invalid_error():
    """Passing an access token to decode_refresh_token raises TokenInvalidError."""
    access_token = create_access_token(
        user_id="U-001", roles=[], permissions=[]
    )
    with pytest.raises(TokenInvalidError):
        decode_refresh_token(access_token)


# ── API Keys ───────────────────────────────────────────────────────────────────

def test_generate_api_key_format():
    """Generated API key has correct format: abhedya_<prefix>_<secret>."""
    new_key = generate_api_key()
    assert new_key.raw_key.startswith("abhedya_")
    parts = new_key.raw_key.split("_")
    assert len(parts) == 3
    assert parts[0] == "abhedya"


def test_api_key_verification():
    """Generated key verifies against stored hash."""
    new_key = generate_api_key()
    assert verify_api_key(new_key.raw_key, new_key.key_hash)


def test_api_key_wrong_key_fails():
    """Wrong key does not verify against stored hash."""
    new_key = generate_api_key()
    other_key = generate_api_key()
    assert not verify_api_key(other_key.raw_key, new_key.key_hash)


def test_api_key_prefix_extraction():
    """Prefix can be extracted from raw key."""
    new_key = generate_api_key()
    prefix = extract_prefix(new_key.raw_key)
    assert prefix == new_key.key_prefix


# ── Permissions / RBAC ─────────────────────────────────────────────────────────

def test_safety_officer_has_risk_run():
    """Safety Officer role includes risk.run permission."""
    perms = get_permissions_for_roles(["SAFETY_OFFICER"])
    assert Permission.RISK_RUN in perms


def test_system_admin_has_all_permissions():
    """SYSTEM_ADMIN has every permission."""
    perms = get_permissions_for_roles(["SYSTEM_ADMIN"])
    for perm in Permission:
        assert perm in perms, f"Missing permission: {perm.value}"


def test_contractor_has_limited_permissions():
    """Contractor has minimal read-only permissions."""
    perms = get_permissions_for_roles(["CONTRACTOR"])
    assert Permission.INCIDENT_READ in perms
    assert Permission.ADMIN_USERS_WRITE not in perms
    assert Permission.EMERGENCY_ACTIVATE not in perms


def test_multi_role_union_permissions():
    """Multi-role resolution returns union of all role permissions."""
    perms = get_permissions_for_roles(["CONTRACTOR", "MAINTENANCE_TECHNICIAN"])
    assert Permission.INCIDENT_READ in perms
    assert Permission.DOCUMENT_READ in perms
    assert Permission.INCIDENT_UPDATE in perms


# ── Principal ──────────────────────────────────────────────────────────────────

def test_principal_has_permission():
    """Principal.has_permission checks permission set."""
    perms = get_permissions_for_roles(["SAFETY_OFFICER"])
    principal = Principal(
        principal_type=PrincipalType.USER,
        user_id="U-001",
        roles=["SAFETY_OFFICER"],
        permissions=perms,
    )
    assert principal.has_permission(Permission.RISK_RUN)
    assert not principal.has_permission(Permission.ADMIN_USERS_WRITE)


def test_principal_has_any_permission():
    """has_any_permission returns True if at least one matches."""
    perms = get_permissions_for_roles(["SHIFT_SUPERVISOR"])
    principal = Principal(
        principal_type=PrincipalType.USER,
        user_id="U-002",
        roles=["SHIFT_SUPERVISOR"],
        permissions=perms,
    )
    assert principal.has_any_permission(Permission.INCIDENT_READ, Permission.EMERGENCY_ACTIVATE)
    assert not principal.has_any_permission(Permission.EMERGENCY_ACTIVATE, Permission.ADMIN_SETTINGS)


# ── Auth Service — Login ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(auth_service, store):
    """Valid credentials return a JWT token pair."""
    tokens = await auth_service.login(
        LoginRequest(username="admin", password="Admin@12345!")
    )
    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "Bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_raises(auth_service):
    """Wrong password raises AuthenticationError."""
    with pytest.raises(AuthenticationError):
        await auth_service.login(
            LoginRequest(username="admin", password="WrongPassword!")
        )


@pytest.mark.asyncio
async def test_login_unknown_user_raises(auth_service):
    """Unknown username raises AuthenticationError."""
    with pytest.raises(AuthenticationError):
        await auth_service.login(
            LoginRequest(username="nobody", password="password123!")
        )


@pytest.mark.asyncio
async def test_login_creates_session(auth_service, store):
    """Login creates a server-side session record."""
    tokens = await auth_service.login(
        LoginRequest(username="safety_officer", password="Safety@12345!")
    )
    # Decode refresh token to get session_id
    payload = decode_refresh_token(tokens.refresh_token)
    session = store.get_session(payload["sid"])
    assert session is not None
    assert session.user_id is not None
    assert not session.revoked


# ── Auth Service — Refresh ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_token_refresh_returns_new_pair(auth_service):
    """Refresh token produces a new access + refresh token pair."""
    tokens = await auth_service.login(
        LoginRequest(username="admin", password="Admin@12345!")
    )
    new_tokens = await auth_service.refresh(tokens.refresh_token)
    assert new_tokens.access_token != tokens.access_token
    assert new_tokens.refresh_token != tokens.refresh_token


@pytest.mark.asyncio
async def test_token_refresh_rotates_session(auth_service, store):
    """Old session is revoked after refresh (token rotation)."""
    tokens = await auth_service.login(
        LoginRequest(username="admin", password="Admin@12345!")
    )
    old_payload = decode_refresh_token(tokens.refresh_token)
    old_session_id = old_payload["sid"]

    await auth_service.refresh(tokens.refresh_token)

    old_session = store.get_session(old_session_id)
    assert old_session.revoked is True


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_raises(auth_service):
    """Invalid refresh token raises TokenInvalidError."""
    with pytest.raises((TokenInvalidError, TokenExpiredError)):
        await auth_service.refresh("invalid.token.here")


# ── Auth Service — User Operations ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_returns_profile(auth_service, store):
    """get_me returns the user's profile and permissions."""
    user = store.get_user_by_username("admin")
    profile = await auth_service.get_me(user.user_id)
    assert profile.username == "admin"
    assert "SYSTEM_ADMIN" in profile.roles
    assert len(profile.permissions) > 0


@pytest.mark.asyncio
async def test_create_user_success(auth_service, store):
    """Admin can create a new user with assigned roles."""
    from app.modules.auth.schemas import CreateUserRequest
    req = CreateUserRequest(
        username="new_tech",
        email="tech2@example.com",
        full_name="New Technician",
        password="Tech@Secure123!",
        roles=["MAINTENANCE_TECHNICIAN"],
        plant_id="PLANT-001",
    )
    profile = await auth_service.create_user(req)
    assert profile.username == "new_tech"
    assert "MAINTENANCE_TECHNICIAN" in profile.roles


@pytest.mark.asyncio
async def test_create_duplicate_user_raises(auth_service):
    """Creating a user with an existing username raises ConflictError."""
    from app.api.exceptions import ConflictError
    from app.modules.auth.schemas import CreateUserRequest
    req = CreateUserRequest(
        username="admin",  # Already exists
        email="dupe@example.com",
        full_name="Duplicate",
        password="Duplicate@123!",
        roles=[],
    )
    with pytest.raises(ConflictError):
        await auth_service.create_user(req)


# ── API Key Management ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_api_key(auth_service, store):
    """API key creation returns raw_key (shown once) and stores hash."""
    req = CreateApiKeyRequest(name="Test Integration", roles=["AI_AGENT"], expires_days=30)
    result = await auth_service.create_api_key(req, owner_id="U-001")
    assert result.raw_key is not None
    assert result.raw_key.startswith("abhedya_")
    assert result.key_prefix in result.raw_key

    # Verify stored hash matches raw key
    stored = store.get_api_key_by_hash(
        __import__("hashlib").sha256(result.raw_key.encode()).hexdigest()
    )
    assert stored is not None
    assert stored.name == "Test Integration"
