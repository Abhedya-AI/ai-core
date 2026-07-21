"""
Sprint 1 — Foundation smoke tests.

These tests verify the application starts and key endpoints respond correctly.
No database connections are required — they return a degraded status when
services are unreachable, which is the expected behaviour in CI.
"""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """GET / should return 200 with app name and status."""
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "ABHEDYA AI Core"
    assert body["status"] == "running"
    assert body["version"] == "1.0.0"


def test_health_endpoint(client: TestClient):
    """GET /health should return 200 regardless of DB connectivity."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert body["status"] in ("healthy", "degraded")
    assert "services" in body
    assert set(body["services"].keys()) == {"postgres", "neo4j", "redis"}


def test_api_v1_health_endpoint(client: TestClient):
    """GET /api/v1/health should mirror GET /health."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "services" in body


def test_swagger_docs_available(client: TestClient):
    """GET /docs should serve the Swagger UI."""
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_health_probes(client: TestClient):
    """GET /health/live, /health/ready, /health/startup should respond properly."""
    live_resp = client.get("/health/live")
    assert live_resp.status_code == 200
    assert live_resp.json()["status"] == "alive"

    ready_resp = client.get("/health/ready")
    assert ready_resp.status_code in (200, 503)
    assert ready_resp.json()["status"] in ("ready", "not_ready")

    startup_resp = client.get("/health/startup")
    assert startup_resp.status_code in (200, 503)
    assert "status" in startup_resp.json()

