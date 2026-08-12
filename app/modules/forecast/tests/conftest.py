from __future__ import annotations
import pytest
import numpy as np
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def sample_time_series():
    """Generate realistic equipment health time series."""
    t = np.linspace(0, 4*np.pi, 100)
    trend = -0.001 * np.arange(100)  # gradual degradation
    seasonal = 0.05 * np.sin(t)       # operational cycle
    noise = np.random.normal(0, 0.02, 100)
    return list(0.85 + trend + seasonal + noise)

@pytest.fixture
def sample_timestamps():
    return [datetime(2026, 1, 1, h % 24, 0, 0, tzinfo=timezone.utc).isoformat() for h in range(100)]

@pytest.fixture
def sample_equipment_context():
    return {
        "equipment_id": "EQ-001",
        "equipment_type": "PUMP",
        "equipment_name": "Primary Feed Pump",
        "current_health": 0.72,
        "sensor_trends": [0.85, 0.84, 0.82, 0.80, 0.77, 0.75, 0.72],
        "maintenance_history": [
            {"date": "2026-01-15", "type": "PREVENTIVE", "health_restored": 0.15}
        ],
        "horizon_hours": 24
    }

@pytest.fixture
def sample_worker_context():
    return {
        "worker_id": "W-001",
        "worker_count": 15,
        "current_zone_id": "ZONE-A",
        "current_hour": 10,
        "horizon_hours": 24
    }

@pytest.fixture
def sample_zone_context():
    return {
        "zone_id": "ZONE-A",
        "zone_name": "Production Zone A",
        "worker_count": 8,
        "equipment_ids": ["EQ-001", "EQ-002", "EQ-003"],
        "sensor_data": {"temperature": 35.0, "gas_ppm": 50.0, "dust_ppm": 120.0},
        "horizon_hours": 24
    }

@pytest.fixture
def mock_graphrag_service():
    service = AsyncMock()
    service.answer = AsyncMock(return_value=MagicMock(
        answer="Historical maintenance records show 3 similar failure patterns.",
        citations=[],
        latency_ms=50
    ))
    return service

@pytest.fixture
def mock_knowledge_service():
    service = AsyncMock()
    return service

@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    repo.save_forecast = AsyncMock(return_value=None)
    repo.get_forecast = AsyncMock(return_value=None)
    repo.get_latest_forecast = AsyncMock(return_value=None)
    repo.list_forecasts = AsyncMock(return_value=[])
    repo.count_forecasts = AsyncMock(return_value=0)
    return repo

@pytest.fixture
def mock_event_publisher():
    publisher = AsyncMock()
    publisher.publish_forecast_generated = AsyncMock(return_value=None)
    publisher.publish_forecast_completed = AsyncMock(return_value=None)
    publisher.publish_threshold_exceeded = AsyncMock(return_value=None)
    publisher.publish_maintenance_forecast_created = AsyncMock(return_value=None)
    publisher.publish_resource_forecast_created = AsyncMock(return_value=None)
    return publisher
