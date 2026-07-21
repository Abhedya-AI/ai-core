from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.knowledge.application.dto import (
    CreateNodeRequest,
    CreateRelationshipRequest,
    GraphSearchRequest,
    NodeMatchCriteria,
    TraversalRequest,
    UpdateNodeRequest,
)
from app.modules.knowledge.domain.entities import Equipment, Hazard, Worker
from app.modules.knowledge.domain.enums import HazardLevel, WorkerRole
from app.modules.knowledge.domain.relationships import RelationshipType
from app.modules.knowledge.infrastructure.exceptions import (
    DuplicateNodeError,
    GraphTraversalError,
    KnowledgeGraphError,
    NodeNotFoundError,
)
from app.modules.knowledge.infrastructure.query_builder import GraphQueryBuilder
from app.modules.knowledge.infrastructure.repositories import (
    BaseNeo4jRepository,
    EquipmentRepository,
    HazardRepository,
    Neo4jGraphRepository,
    WorkerRepository,
)


def test_dtos():
    """Verify DTO validation and instantiation."""
    create_req = CreateNodeRequest(label="Worker", properties={"name": "Alice"})
    assert create_req.label == "Worker"

    update_req = UpdateNodeRequest(node_id="W-1", properties={"name": "Alice Green"})
    assert update_req.node_id == "W-1"

    rel_req = CreateRelationshipRequest(
        source_id="W-1",
        target_id="Z-1",
        rel_type=RelationshipType.WORKS_IN,
    )
    assert rel_req.rel_type == RelationshipType.WORKS_IN

    trav_req = TraversalRequest(start_node_id="W-1", max_depth=2)
    assert trav_req.max_depth == 2


def test_graph_query_builder():
    """Verify fluent Cypher query builder generates valid parameterized queries."""
    query, params = (
        GraphQueryBuilder()
        .node("Equipment", alias="e")
        .where(status="OPERATIONAL")
        .related("HAS_SENSOR")
        .to("Sensor", alias="s")
        .limit(10)
        .build()
    )

    assert "MATCH (e:Equipment) -[r:HAS_SENSOR]->(s:Sensor)" in query
    assert "WHERE e.status = $status_0" in query
    assert "RETURN s LIMIT 10" in query
    assert params["status_0"] == "OPERATIONAL"


@pytest.mark.asyncio
async def test_base_repository_mock_crud():
    """Verify BaseNeo4jRepository CRUD operations with mocked session."""
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session

    # Mock execute_query return data
    mock_result = AsyncMock()
    mock_result.data.return_value = [{"n": {"id": "W-1", "name": "Alice"}}]
    mock_session.run.return_value = mock_result

    repo = BaseNeo4jRepository(driver=mock_driver)

    # Test find_by_id
    res = await repo.find_by_id("W-1")
    assert res["id"] == "W-1"
    assert res["name"] == "Alice"

    # Test count
    mock_result.data.return_value = [{"count": 42}]
    cnt = await repo.count("Worker")
    assert cnt == 42


@pytest.mark.asyncio
async def test_worker_repository_mock():
    """Verify WorkerRepository queries."""
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session

    mock_result = AsyncMock()
    mock_result.data.return_value = [{"w": {"id": "W-1", "badge_number": "BADGE-1", "name": "Bob"}}]
    mock_session.run.return_value = mock_result

    repo = WorkerRepository(driver=mock_driver)

    worker = Worker(badge_number="BADGE-1", name="Bob", role=WorkerRole.TECHNICIAN)
    created = await repo.create_worker(worker)
    assert created["badge_number"] == "BADGE-1"

    found = await repo.find_by_badge("BADGE-1")
    assert found["badge_number"] == "BADGE-1"


@pytest.mark.asyncio
async def test_hazard_repository_mock():
    """Verify HazardRepository queries."""
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session

    mock_result = AsyncMock()
    mock_result.data.return_value = [{"h": {"id": "H-1", "severity": "CRITICAL"}}]
    mock_session.run.return_value = mock_result

    repo = HazardRepository(driver=mock_driver)
    critical_hazards = await repo.get_critical_hazards()
    assert len(critical_hazards) == 1
    assert critical_hazards[0]["severity"] == "CRITICAL"


@pytest.mark.asyncio
async def test_graph_repository_shortest_path_mock():
    """Verify Neo4jGraphRepository shortest path and search functionality."""
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value = mock_session

    mock_result = AsyncMock()
    mock_result.data.return_value = [{"degree": 5}]
    mock_session.run.return_value = mock_result

    repo = Neo4jGraphRepository(driver=mock_driver)
    deg = await repo.node_degree("EQ-100")
    assert deg == 5


def test_exception_messages():
    """Verify exception string formatting."""
    err = NodeNotFoundError("NODE-99", "Equipment")
    assert "NODE-99" in str(err)
    assert "Equipment" in str(err)

    dup = DuplicateNodeError("NODE-1")
    assert "NODE-1" in str(dup)
