"""
Pytest root configuration.

Shared fixtures go here so they are available to all test modules.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="session")
def client():
    """Synchronous test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c
