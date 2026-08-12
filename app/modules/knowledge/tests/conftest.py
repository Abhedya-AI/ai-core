"""
conftest.py — Test Fixtures for Knowledge Graph Platform.
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.modules.auth.jwt import create_access_token
from app.modules.knowledge.domain.entities import Equipment, Hazard, Incident, Sensor, Worker, Zone
from app.modules.knowledge.domain.enums import HazardLevel, SensorType, WorkerRole
from main import app


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Return Authorization header with a valid test JWT."""
    token = create_access_token(
        user_id="test_user_001",
        roles=["admin"],
        permissions=["graph.read", "graph.write"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient instance."""
    return TestClient(app)


@pytest.fixture
def mock_neo4j_session() -> AsyncMock:
    """Mock Neo4j AsyncSession."""
    session = AsyncMock()
    result = AsyncMock()
    result.data = AsyncMock(return_value=[])
    result.single = AsyncMock(return_value=None)
    session.run = AsyncMock(return_value=result)
    return session


@pytest.fixture
def sample_worker() -> Worker:
    return Worker(
        id="worker-test-01",
        name="Ravi Kumar",
        badge_number="B-101",
        role=WorkerRole.OPERATOR,
        email="ravi@abhedya.ai",
        department="Operations",
    )


@pytest.fixture
def sample_equipment() -> Equipment:
    return Equipment(
        id="equip-test-01",
        name="Boiler 3",
        code="EQ-BLR3",
        equipment_type="BOILER",
        status="OPERATIONAL",
    )


@pytest.fixture
def sample_sensor() -> Sensor:
    return Sensor(
        id="sensor-test-01",
        name="Pressure Sensor P-01",
        sensor_type=SensorType.PRESSURE,
        unit="PSI",
        status="ACTIVE",
    )


@pytest.fixture
def sample_zone() -> Zone:
    return Zone(
        id="zone-test-01",
        name="Boiler Room Alpha",
        code="Z-BOILER-A",
        risk_score=75.0,
    )


@pytest.fixture
def sample_hazard() -> Hazard:
    return Hazard(
        id="hazard-test-01",
        title="High Pressure Anomaly",
        description="Pressure exceeded safety threshold",
        zone_id="zone-test-01",
        severity=HazardLevel.HIGH,
    )


@pytest.fixture
def sample_incident() -> Incident:
    return Incident(
        id="incident-test-01",
        title="Steam Breach Warning",
        description="Minor steam leak detected",
        zone_id="zone-test-01",
        status="OPEN",
        severity="HIGH",
    )
