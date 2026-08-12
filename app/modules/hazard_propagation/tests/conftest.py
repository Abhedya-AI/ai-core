from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def sample_graph_nodes():
    return [
        {"node_id": "NODE-1", "node_type": "ZONE", "label": "Zone A", "coordinates": {"x": 0.0, "y": 0.0}},
        {"node_id": "NODE-2", "node_type": "ZONE", "label": "Zone B", "coordinates": {"x": 10.0, "y": 0.0}},
        {"node_id": "NODE-3", "node_type": "EQUIPMENT", "label": "Pump A", "coordinates": {"x": 5.0, "y": 5.0}},
        {"node_id": "NODE-4", "node_type": "ZONE", "label": "Zone C", "coordinates": {"x": 0.0, "y": 10.0}},
        {"node_id": "NODE-5", "node_type": "ZONE", "label": "Safe Zone", "coordinates": {"x": 20.0, "y": 20.0}},
    ]

@pytest.fixture
def sample_graph_edges():
    return [
        {"edge_id": "E1", "source_node_id": "NODE-1", "target_node_id": "NODE-2", "resistance": 0.1, "distance_meters": 10.0, "edge_type": "ADJACENCY"},
        {"edge_id": "E2", "source_node_id": "NODE-1", "target_node_id": "NODE-4", "resistance": 0.2, "distance_meters": 10.0, "edge_type": "ADJACENCY"},
        {"edge_id": "E3", "source_node_id": "NODE-2", "target_node_id": "NODE-3", "resistance": 0.3, "distance_meters": 7.0, "edge_type": "PIPE"},
        {"edge_id": "E4", "source_node_id": "NODE-4", "target_node_id": "NODE-5", "resistance": 0.0, "distance_meters": 15.0, "edge_type": "ADJACENCY"},
    ]

@pytest.fixture
def sample_propagation_context():
    return {
        "hazard_type": "FIRE",
        "source_node_id": "NODE-1",
        "initial_intensity": 0.8,
        "wind_speed_ms": 2.0,
        "wind_direction_deg": 90.0,
        "fuel_load": 0.6,
    }

@pytest.fixture
def mock_graphrag_service():
    service = AsyncMock()
    service.answer = AsyncMock(return_value=MagicMock(
        answer="Historical records show similar fires were contained using firewall isolation.",
        citations=[],
        latency_ms=50
    ))
    return service

@pytest.fixture
def mock_knowledge_service():
    return AsyncMock()

@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    for method in ['save_propagation', 'save_exposure', 'save_containment_plan', 'save_evacuation', 'save_simulation', 'save_cascade']:
        setattr(repo, method, AsyncMock(return_value=None))
    repo.get_propagation = AsyncMock(return_value=None)
    repo.list_propagations = AsyncMock(return_value=[])
    repo.count_propagations = AsyncMock(return_value=0)
    repo.get_exposure = AsyncMock(return_value=None)
    repo.get_containment_plan = AsyncMock(return_value=None)
    repo.get_evacuation = AsyncMock(return_value=None)
    repo.get_simulation = AsyncMock(return_value=None)
    repo.get_cascade = AsyncMock(return_value=None)
    return repo

@pytest.fixture
def mock_event_publisher():
    publisher = AsyncMock()
    for method in ['publish_hazard_detected', 'publish_propagation_started', 'publish_propagation_updated',
                   'publish_exposure_threshold_exceeded', 'publish_containment_generated',
                   'publish_evacuation_generated', 'publish_cascade_detected',
                   'publish_simulation_completed', 'publish_propagation_completed']:
        setattr(publisher, method, AsyncMock(return_value=None))
    return publisher
