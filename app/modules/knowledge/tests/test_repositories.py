"""
test_repositories.py — Repository Unit Tests.
"""
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.knowledge.application.dto import CreateNodeRequest, CreateRelationshipRequest
from app.modules.knowledge.domain.relationships import RelationshipType
from app.modules.knowledge.infrastructure.repositories.analytics_repository import AnalyticsRepository
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.knowledge.infrastructure.repositories.history_repository import HistoryRepository
from app.modules.knowledge.infrastructure.repositories.ontology_repository import OntologyRepository
from app.modules.knowledge.infrastructure.repositories.traversal_repository import TraversalRepository


@pytest.mark.asyncio
async def test_base_repository_create_node():
    repo = BaseNeo4jRepository()
    mock_records = [{"n": {"id": "w-1", "name": "Ravi", "entity_type": "Worker"}}]
    with patch.object(repo, "execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_records
        req = CreateNodeRequest(label="Worker", properties={"name": "Ravi"}, node_id="w-1")
        res = await repo.create_node(req)
        assert res["id"] == "w-1"
        mock_exec.assert_called_once()


@pytest.mark.asyncio
async def test_base_repository_exists():
    repo = BaseNeo4jRepository()
    with patch.object(repo, "execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = [{"exists": True}]
        exists = await repo.exists("w-1")
        assert exists is True


@pytest.mark.asyncio
async def test_traversal_repository_bfs():
    repo = TraversalRepository()
    mock_records = [
        {"n": {"id": "z-1", "name": "Zone 1"}, "depth": 1, "path_ids": ["w-1", "z-1"]}
    ]
    with patch.object(repo, "execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_records
        res = await repo.bfs_traverse("w-1", max_depth=2)
        assert len(res) == 1
        assert res[0]["depth"] == 1
        assert res[0]["node"]["id"] == "z-1"


@pytest.mark.asyncio
async def test_traversal_repository_neighborhood():
    repo = TraversalRepository()
    mock_records = [
        {
            "neighbor": {"id": "eq-1", "name": "Boiler 3", "entity_type": "Equipment"},
            "rel_type": "MONITORS",
            "rel_props": {},
        }
    ]
    with patch.object(repo, "execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_records
        res = await repo.get_neighborhood("s-1", hops=1)
        assert res["center_id"] == "s-1"
        assert len(res["nodes"]) == 1
        assert len(res["edges"]) == 1


@pytest.mark.asyncio
async def test_analytics_repository_degree():
    repo = AnalyticsRepository()
    mock_records = [
        {"node_id": "eq-1", "label": "Equipment", "name": "Boiler 3", "degree": 5}
    ]
    with patch.object(repo, "execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_records
        res = await repo.degree_centrality(label="Equipment")
        assert len(res) == 1
        assert res[0]["score"] == 5.0
        assert res[0]["rank"] == 1


@pytest.mark.asyncio
async def test_ontology_repository_all_labels():
    repo = OntologyRepository()
    with patch.object(repo, "execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = [{"label": "Worker"}, {"label": "Equipment"}]
        labels = await repo.get_all_labels()
        assert "Worker" in labels
        assert "Equipment" in labels


@pytest.mark.asyncio
async def test_history_repository_diff():
    diffs = HistoryRepository.compute_diff(
        {"name": "Boiler 3", "status": "OPERATIONAL", "temp": 100},
        {"name": "Boiler 3", "status": "WARNING", "temp": 150},
    )
    assert len(diffs) == 2
    diff_keys = {d["property_name"] for d in diffs}
    assert "status" in diff_keys
    assert "temp" in diff_keys
