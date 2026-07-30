"""
tests/test_api_gateway.py — API Gateway Middleware and Endpoint Tests.

Covers:
  - Request ID propagation (X-Request-ID header)
  - Rate limit headers (X-RateLimit-*)
  - Error handler converts unhandled exceptions → ErrorResponse
  - /auth/login and /auth/me endpoints (end-to-end)
  - /incidents CRUD with auth enforcement
  - /workflows execution with auth enforcement
  - /admin/users admin-only access
  - Health endpoint accessibility
  - Permission denied → 403 response
  - Unauthenticated → 401 response
"""

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from main import app


@pytest.fixture(scope="module")
def client():
    """TestClient for the full ABHEDYA app."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="module")
def admin_token(client):
    """Log in as admin and return access token."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "Admin@12345!",
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["data"]["access_token"]


@pytest.fixture(scope="module")
def safety_token(client):
    """Log in as safety officer and return access token."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "safety_officer",
        "password": "Safety@12345!",
    })
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


@pytest.fixture(scope="module")
def contractor_token(client):
    """Log in as contractor and return access token."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "technician",
        "password": "Tech@12345!",
    })
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


# ── Health ─────────────────────────────────────────────────────────────────────

def test_root_returns_200(client):
    """Root endpoint returns application identity."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert data["version"] == "4.0.0"


def test_health_live(client):
    """GET /health returns 200."""
    resp = client.get("/health")
    assert resp.status_code == 200


# ── Middleware: Request ID ─────────────────────────────────────────────────────

def test_request_id_header_present(client):
    """Every response includes X-Request-ID header."""
    resp = client.get("/")
    assert "x-request-id" in resp.headers


def test_request_id_propagated_from_client(client):
    """Client-supplied X-Request-ID is echoed back."""
    my_id = "test-trace-12345"
    resp = client.get("/", headers={"X-Request-ID": my_id})
    assert resp.headers.get("x-request-id") == my_id


def test_response_time_header_present(client):
    """Every response includes X-Response-Time-Ms header."""
    resp = client.get("/")
    assert "x-response-time-ms" in resp.headers


# ── Auth: Login ────────────────────────────────────────────────────────────────

def test_login_success_returns_tokens(client):
    """POST /auth/login with valid credentials returns token pair."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "Admin@12345!",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]
    assert body["metadata"]["trace_id"]


def test_login_wrong_password_returns_401(client):
    """POST /auth/login with wrong password (valid length) returns 401."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "WrongPassword123!",  # 8+ chars to pass schema validation
    })
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"


def test_login_unknown_user_returns_401(client):
    """POST /auth/login with unknown user returns 401."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "doesnotexist",
        "password": "doesnotmatter123!",
    })
    assert resp.status_code == 401


def test_login_missing_field_returns_422(client):
    """POST /auth/login with missing password returns 422 (Pydantic validation)."""
    resp = client.post("/api/v1/auth/login", json={"username": "admin"})
    # FastAPI's built-in RequestValidationError handler fires before middleware
    assert resp.status_code == 422


# ── Auth: Token Refresh ────────────────────────────────────────────────────────

def test_refresh_token_returns_new_pair(client):
    """POST /auth/refresh returns new token pair."""
    login = client.post("/api/v1/auth/login", json={
        "username": "plant_manager",
        "password": "Manager@12345!",
    })
    refresh_token = login.json()["data"]["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["access_token"] != login.json()["data"]["access_token"]


# ── Auth: /me ──────────────────────────────────────────────────────────────────

def test_get_me_authenticated(client, admin_token):
    """GET /auth/me with valid token returns user profile."""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["username"] == "admin"
    assert "SYSTEM_ADMIN" in body["data"]["roles"]
    assert len(body["data"]["permissions"]) > 0


def test_get_me_unauthenticated_returns_401(client):
    """GET /auth/me without token returns 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False


# ── Incidents ──────────────────────────────────────────────────────────────────

def test_create_incident_authorized(client, safety_token):
    """POST /incidents with INCIDENT_CREATE permission succeeds."""
    resp = client.post(
        "/api/v1/incidents",
        json={
            "title": "Gas leak in Tank T-07",
            "description": "Detected methane gas leak near Tank T-07 in Zone B",
            "zone_id": "ZONE-B",
            "target_entity_id": "TANK-T07",
            "severity": "HIGH",
            "auto_investigate": False,  # Skip AI for speed in tests
        },
        headers={"Authorization": f"Bearer {safety_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "OPEN"
    assert body["data"]["title"] == "Gas leak in Tank T-07"


def test_create_incident_unauthenticated_returns_401(client):
    """POST /incidents without token returns 401."""
    resp = client.post("/api/v1/incidents", json={
        "title": "Test",
        "description": "Test description for incident",
    })
    assert resp.status_code == 401


def test_list_incidents_authorized(client, safety_token):
    """GET /incidents returns incident list."""
    resp = client.get(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {safety_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert "pagination" in body


def test_get_incident_not_found_returns_404(client, safety_token):
    """GET /incidents/{id} with unknown ID returns 404."""
    resp = client.get(
        "/api/v1/incidents/does-not-exist-001",
        headers={"Authorization": f"Bearer {safety_token}"},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "RESOURCE_NOT_FOUND"


# ── Workflows ──────────────────────────────────────────────────────────────────

def test_run_workflow_authorized(client, safety_token):
    """POST /workflows with WORKFLOW_EXECUTE permission runs and returns results."""
    resp = client.post(
        "/api/v1/workflows",
        json={
            "query": "Assess risk of temperature anomaly in Tank T-12",
            "zone_id": "ZONE-A",
            "target_entity_id": "TANK-T12",
        },
        headers={"Authorization": f"Bearer {safety_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] in ("COMPLETED", "FAILED")
    assert body["data"]["task_id"]


def test_get_workflow_not_found(client, safety_token):
    """GET /workflows/{id} with unknown ID returns 404."""
    resp = client.get(
        "/api/v1/workflows/non-existent-task-id",
        headers={"Authorization": f"Bearer {safety_token}"},
    )
    assert resp.status_code == 404


# ── Admin ──────────────────────────────────────────────────────────────────────

def test_admin_list_users_admin_only(client, admin_token):
    """GET /admin/users returns user list for SYSTEM_ADMIN."""
    resp = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1


def test_admin_list_users_permission_denied_for_technician(client, contractor_token):
    """GET /admin/users returns 403 for MAINTENANCE_TECHNICIAN role."""
    resp = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {contractor_token}"},
    )
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["code"] == "AUTHZ_PERMISSION_DENIED"


def test_admin_create_user(client, admin_token):
    """POST /admin/users creates a new user (admin only)."""
    resp = client.post(
        "/api/v1/admin/users",
        json={
            "username": "new_auditor_01",
            "email": "newauditor@example.com",
            "full_name": "New Auditor",
            "password": "Auditor@Secure123!",
            "roles": ["AUDITOR"],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["username"] == "new_auditor_01"


def test_admin_get_audit_log(client, admin_token):
    """GET /admin/audit returns audit log entries for admin."""
    resp = client.get(
        "/api/v1/admin/audit",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["data"], list)
    # At least our login events should be in there
    assert len(body["data"]) >= 1


# ── Error Handler ──────────────────────────────────────────────────────────────

def test_invalid_json_returns_422(client):
    """Malformed JSON body returns 422 with error envelope."""
    resp = client.post(
        "/api/v1/auth/login",
        content=b"not json at all",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422


# ── Rate Limit Headers ─────────────────────────────────────────────────────────

def test_rate_limit_headers_present(client, admin_token):
    """Authenticated requests include X-RateLimit headers."""
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert "x-ratelimit-limit" in resp.headers
    assert "x-ratelimit-remaining" in resp.headers


# ── Standard Response Structure ────────────────────────────────────────────────

def test_success_response_envelope(client, admin_token):
    """All success responses follow the StandardResponse envelope."""
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    body = resp.json()
    assert "success" in body
    assert "data" in body
    assert "metadata" in body
    assert "trace_id" in body["metadata"]
    assert "request_id" in body["metadata"]
    assert "timestamp" in body["metadata"]
