from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_twin_state():
    return {
        "plant_id": "plant-001",
        "zone_states": {"zone-001": {"zone_id": "zone-001", "health_score": 0.85, "risk_score": 0.2, "occupancy": 5, "max_occupancy": 20, "is_hazard_active": False, "entity_type": "ZONE"}},
        "equipment_states": {"eq-001": {"equipment_id": "eq-001", "health_score": 0.9, "risk_score": 0.1, "utilization_pct": 0.7, "status": "ACTIVE", "entity_type": "EQUIPMENT", "dependency_ids": []}},
        "worker_states": {"w-001": {"worker_id": "w-001", "current_zone_id": "zone-001", "safety_score": 0.9, "exposure_risk_score": 0.1, "entity_type": "WORKER"}},
        "sensor_states": {"s-001": {"sensor_id": "s-001", "current_value": 22.5, "is_online": True, "health_score": 0.95, "entity_type": "SENSOR"}},
        "camera_states": {},
        "hazard_states": {},
        "resource_states": {"r-001": {"resource_id": "r-001", "quantity_available": 80.0, "quantity_total": 100.0, "entity_type": "RESOURCE"}},
    }

@pytest.fixture
def mock_graphrag():
    mock = AsyncMock()
    mock.answer = AsyncMock(return_value=MagicMock(answer="Test answer", citations=["ref-1"]))
    return mock

@pytest.fixture
def mock_orchestration_service(mock_twin_state):
    svc = AsyncMock()
    svc.get_twin = AsyncMock(return_value={"twin_id": "twin-001", "plant_id": "plant-001", "status": "ACTIVE"})
    svc.get_state = AsyncMock(return_value={"entities": mock_twin_state, "total_count": 4})
    svc.run_simulation = AsyncMock(return_value={"simulation_id": "sim-001", "status": "COMPLETED", "confidence": 0.85})
    return svc
