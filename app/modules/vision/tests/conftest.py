"""
conftest.py — Vision Safety Intelligence Test Fixtures.
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.modules.auth.jwt import create_access_token
from main import app


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Return Authorization header with a valid test JWT."""
    token = create_access_token(
        user_id="test_vision_user",
        roles=["admin"],
        permissions=["graph.read", "graph.write"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient instance."""
    return TestClient(app)
