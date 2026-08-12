"""
test_events.py — Graph Events Unit Tests.
"""
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.knowledge.events.graph_events import (
    NodeCreatedEvent, NodeDeletedEvent, NodeUpdatedEvent,
    RelationshipCreatedEvent, Topics, publish_graph_event,
    publish_node_created, publish_node_deleted, publish_node_updated,
    publish_relationship_created
)


def test_event_dataclass_serialization():
    evt = NodeCreatedEvent.new(node_id="w-100", label="Worker", properties={"name": "Alice"})
    d = evt.to_dict()
    assert d["node_id"] == "w-100"
    assert d["label"] == "Worker"
    assert d["event_type"] == "NodeCreated"
    assert d["source_module"] == "knowledge_graph"
    assert "event_id" in d
    assert "timestamp" in d


@pytest.mark.asyncio
async def test_publish_graph_event():
    evt = NodeCreatedEvent.new(node_id="w-100", label="Worker", properties={"name": "Alice"})
    mock_bus = AsyncMock()
    mock_bus.publish.return_value = True

    with patch("app.infrastructure.kafka.producer.EventBus.get", return_value=mock_bus):
        ok = await publish_graph_event(evt, Topics.NODE_CREATED)
        assert ok is True
        mock_bus.publish.assert_called_once()
        call_kwargs = mock_bus.publish.call_args.kwargs
        assert call_kwargs["topic"] == Topics.NODE_CREATED
        assert call_kwargs["key"] == "w-100"
        assert call_kwargs["payload"]["node_id"] == "w-100"


@pytest.mark.asyncio
async def test_convenience_publishers():
    mock_bus = AsyncMock()
    mock_bus.publish.return_value = True

    with patch("app.infrastructure.kafka.producer.EventBus.get", return_value=mock_bus):
        await publish_node_created("w-1", "Worker", {"name": "Bob"})
        await publish_node_updated("w-1", "Worker", {"name": "Robert"}, version=2)
        await publish_node_deleted("w-1", "Worker")
        await publish_relationship_created("w-1", "z-1", "LOCATED_IN")

        assert mock_bus.publish.call_count == 4
