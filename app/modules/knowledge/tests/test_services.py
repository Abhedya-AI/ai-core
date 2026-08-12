"""
test_services.py — Service Unit Tests.
"""
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.knowledge.application.dto import (
    AnalyticsRequest, ContextRequest, SyncNodeRequest
)
from app.modules.knowledge.services.context_service import ContextService
from app.modules.knowledge.services.graph_analytics_service import GraphAnalyticsService
from app.modules.knowledge.services.graph_cache_service import GraphCacheService
from app.modules.knowledge.services.graph_search_service import GraphSearchService
from app.modules.knowledge.services.graph_sync_service import GraphSyncService


@pytest.mark.asyncio
async def test_graph_cache_service():
    service = GraphCacheService()
    with patch.object(service._cache, "get", new_callable=AsyncMock) as mock_get, \
         patch.object(service._cache, "set", new_callable=AsyncMock) as mock_set:
        mock_get.return_value = {"id": "n-1", "name": "Test Node"}
        mock_set.return_value = True

        res = await service.get_node("n-1")
        assert res["id"] == "n-1"

        ok = await service.set_node("n-1", {"id": "n-1"})
        assert ok is True


@pytest.mark.asyncio
async def test_context_service_assemble():
    mock_traversal = AsyncMock()
    mock_traversal.get_neighborhood.return_value = {
        "nodes": [
            {"id": "eq-1", "entity_type": "Equipment", "name": "Boiler 3"},
            {"id": "s-1", "entity_type": "Sensor", "name": "Temp Sensor 1"},
        ],
        "edges": [
            {"source_id": "s-1", "target_id": "eq-1", "rel_type": "MONITORS"},
        ],
    }

    mock_cache = AsyncMock()
    mock_cache.get_context.return_value = None

    service = ContextService(traversal_repo=mock_traversal, cache_service=mock_cache)
    req = ContextRequest(node_id="eq-1", depth=2)
    ctx = await service.assemble_context(req)

    assert ctx.root_node_id == "eq-1"
    assert len(ctx.nodes) == 2
    assert len(ctx.edges) == 1
    assert "Boiler 3" in ctx.narrative
    assert ctx.token_estimate > 0


@pytest.mark.asyncio
async def test_graph_sync_service_sync_node():
    mock_repo = AsyncMock()
    mock_repo.exists.return_value = False
    mock_repo.execute_query.return_value = [{"n": {"id": "s-100"}}]

    service = GraphSyncService(repo=mock_repo)
    req = SyncNodeRequest(
        source_module="sensor",
        node_id="s-100",
        label="Sensor",
        properties={"name": "Gas Sensor 4", "sensor_type": "GAS"},
    )
    res = await service.sync_node(req)
    assert res.nodes_created == 1
    assert res.success is True


@pytest.mark.asyncio
async def test_graph_search_service_text():
    mock_repo = AsyncMock()
    mock_repo.execute_query.side_effect = [
        [{"n": {"id": "eq-1", "name": "Boiler 3", "entity_type": "Equipment"}}],
        [{"total": 1}],
    ]
    service = GraphSearchService(repo=mock_repo)
    from app.modules.knowledge.application.dto import SearchRequest
    req = SearchRequest(query="Boiler")
    res = await service.search(req)

    assert res.total == 1
    assert len(res.hits) == 1
    assert res.hits[0].node_id == "eq-1"


@pytest.mark.asyncio
async def test_graph_analytics_service():
    mock_analytics = AsyncMock()
    mock_analytics.degree_centrality.return_value = [
        {"node_id": "eq-1", "label": "Equipment", "name": "Boiler 3", "score": 10.0, "rank": 1}
    ]
    mock_cache = AsyncMock()
    mock_cache.get_analytics.return_value = None

    service = GraphAnalyticsService(analytics_repo=mock_analytics, cache_service=mock_cache)
    req = AnalyticsRequest(algorithm="degree")
    res = await service.run_analytics(req)

    assert res.centrality is not None
    assert res.centrality.total_nodes == 1
    assert res.centrality.results[0].node_id == "eq-1"
