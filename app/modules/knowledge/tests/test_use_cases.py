"""
test_use_cases.py — Application Layer Use Cases Unit Tests.
"""
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.knowledge.application.dto import (
    AnalyticsRequest, ContextRequest, CreateNodeRequest,
    CreateRelationshipRequest, SearchRequest, SyncNodeRequest, UpdateNodeRequest
)
from app.modules.knowledge.application.use_cases import (
    AssembleContextUseCase, ComputeAnalyticsUseCase, CreateNodeUseCase,
    CreateRelationshipUseCase, DeleteNodeUseCase, FindNodeUseCase,
    SearchKnowledgeGraphUseCase, SyncGraphNodeUseCase, UpdateNodeUseCase
)
from app.modules.knowledge.domain.relationships import RelationshipType


@pytest.mark.asyncio
async def test_create_node_use_case():
    mock_repo = AsyncMock()
    mock_repo.create_node.return_value = {"id": "eq-10", "name": "Pump 1", "entity_type": "Equipment"}
    mock_cache = AsyncMock()

    use_case = CreateNodeUseCase(repo=mock_repo, cache=mock_cache)
    req = CreateNodeRequest(label="Equipment", properties={"name": "Pump 1"}, node_id="eq-10")

    with patch("app.modules.knowledge.application.use_cases.node_use_cases.publish_node_created", new_callable=AsyncMock):
        res = await use_case.execute(req)
        assert res["id"] == "eq-10"
        mock_repo.create_node.assert_called_once()
        mock_cache.set_node.assert_called_once()


@pytest.mark.asyncio
async def test_update_node_use_case():
    mock_repo = AsyncMock()
    mock_repo.find_by_id.return_value = {"id": "eq-10", "name": "Pump 1", "entity_type": "Equipment"}
    mock_repo.update_node.return_value = {"id": "eq-10", "name": "Pump 1 Updated", "entity_type": "Equipment"}
    mock_history = AsyncMock()
    mock_cache = AsyncMock()

    use_case = UpdateNodeUseCase(repo=mock_repo, history=mock_history, cache=mock_cache)
    req = UpdateNodeRequest(node_id="eq-10", properties={"name": "Pump 1 Updated"})

    with patch("app.modules.knowledge.application.use_cases.node_use_cases.publish_node_updated", new_callable=AsyncMock):
        res = await use_case.execute(req)
        assert res["name"] == "Pump 1 Updated"
        mock_history.record_snapshot.assert_called_once()
        mock_cache.invalidate_node.assert_called_once_with("eq-10")


@pytest.mark.asyncio
async def test_delete_node_use_case():
    mock_repo = AsyncMock()
    mock_repo.delete_node.return_value = True
    mock_cache = AsyncMock()

    use_case = DeleteNodeUseCase(repo=mock_repo, cache=mock_cache)
    with patch("app.modules.knowledge.application.use_cases.node_use_cases.publish_node_deleted", new_callable=AsyncMock):
        ok = await use_case.execute("eq-10", label="Equipment")
        assert ok is True
        mock_cache.invalidate_node.assert_called_once_with("eq-10")


@pytest.mark.asyncio
async def test_create_relationship_use_case():
    mock_repo = AsyncMock()
    mock_repo.create_relationship.return_value = True

    use_case = CreateRelationshipUseCase(repo=mock_repo)
    req = CreateRelationshipRequest(source_id="s-1", target_id="eq-1", rel_type=RelationshipType.MONITORS)

    with patch("app.modules.knowledge.application.use_cases.relationship_use_cases.publish_relationship_created", new_callable=AsyncMock):
        ok = await use_case.execute(req)
        assert ok is True


@pytest.mark.asyncio
async def test_compute_analytics_use_case():
    mock_service = AsyncMock()
    use_case = ComputeAnalyticsUseCase(service=mock_service)
    req = AnalyticsRequest(algorithm="degree")
    await use_case.execute(req)
    mock_service.run_analytics.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_assemble_context_use_case():
    mock_service = AsyncMock()
    use_case = AssembleContextUseCase(service=mock_service)
    req = ContextRequest(node_id="eq-1")
    await use_case.execute(req)
    mock_service.assemble_context.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_sync_node_use_case():
    mock_service = AsyncMock()
    use_case = SyncGraphNodeUseCase(service=mock_service)
    req = SyncNodeRequest(source_module="sensor", node_id="s-1", label="Sensor", properties={})
    await use_case.execute(req)
    mock_service.sync_node.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_search_use_case():
    mock_service = AsyncMock()
    use_case = SearchKnowledgeGraphUseCase(service=mock_service)
    req = SearchRequest(query="boiler")
    await use_case.execute(req)
    mock_service.search.assert_called_once_with(req)
