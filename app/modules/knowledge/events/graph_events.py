"""
events/graph_events.py — Knowledge Graph Event Definitions and Publishers.

All graph mutations, traversals, and sync operations publish typed events
through the existing Kafka EventBus (EventBus.get().publish(topic, payload, key)).
Events are also automatically forwarded to the EventBridge for real-time
WebSocket/SSE streaming to connected dashboard clients.

Usage:
    from app.modules.knowledge.events.graph_events import NodeCreatedEvent, publish_node_created

    event = NodeCreatedEvent(
        event_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        node_id=node_id,
        label='Equipment',
        properties={'name': 'Boiler 3'},
    )
    await publish_node_created(event)
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger

log = get_logger("knowledge.events")


# ── Topic Constants ────────────────────────────────────────────────────────────

class Topics:
    """Kafka topic name constants for Knowledge Graph events."""

    NODE_CREATED              = "graph.node.created"
    NODE_UPDATED              = "graph.node.updated"
    NODE_DELETED              = "graph.node.deleted"
    RELATIONSHIP_CREATED      = "graph.relationship.created"
    RELATIONSHIP_DELETED      = "graph.relationship.deleted"
    ONTOLOGY_UPDATED          = "graph.ontology.updated"
    GRAPH_SYNCHRONIZED        = "graph.synchronized"
    GRAPH_VERSION_CREATED     = "graph.version.created"
    GRAPH_TRAVERSAL_COMPLETED = "graph.traversal.completed"
    GRAPH_SEARCH_EXECUTED     = "graph.search.executed"
    GRAPH_ANALYTICS_COMPUTED  = "graph.analytics.computed"


# ── Base Event ─────────────────────────────────────────────────────────────────

@dataclass
class GraphEvent:
    """Base class for all Knowledge Graph domain events."""

    event_id: str
    timestamp: str
    source_module: str = "knowledge_graph"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def new(cls, **kwargs: Any) -> "GraphEvent":
        kwargs.setdefault("event_id", str(uuid.uuid4()))
        kwargs.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        return cls(**kwargs)


# ── Node Events ────────────────────────────────────────────────────────────────

@dataclass
class NodeCreatedEvent(GraphEvent):
    node_id: str = ""
    label: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    event_type: str = "NodeCreated"
    severity: str = "INFO"


@dataclass
class NodeUpdatedEvent(GraphEvent):
    node_id: str = ""
    label: str = ""
    changes: dict[str, Any] = field(default_factory=dict)
    previous_version: int = 0
    event_type: str = "NodeUpdated"
    severity: str = "INFO"


@dataclass
class NodeDeletedEvent(GraphEvent):
    node_id: str = ""
    label: str = ""
    deleted_by: str = ""
    event_type: str = "NodeDeleted"
    severity: str = "INFO"


# ── Relationship Events ────────────────────────────────────────────────────────

@dataclass
class RelationshipCreatedEvent(GraphEvent):
    source_id: str = ""
    target_id: str = ""
    rel_type: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    event_type: str = "RelationshipCreated"
    severity: str = "INFO"


@dataclass
class RelationshipDeletedEvent(GraphEvent):
    source_id: str = ""
    target_id: str = ""
    rel_type: str = ""
    event_type: str = "RelationshipDeleted"
    severity: str = "INFO"


# ── Ontology / Schema Events ───────────────────────────────────────────────────

@dataclass
class OntologyUpdatedEvent(GraphEvent):
    change_type: str = ""        # 'constraint_added', 'index_created', etc.
    entity_type: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    event_type: str = "OntologyUpdated"
    severity: str = "INFO"


# ── Sync Events ────────────────────────────────────────────────────────────────

@dataclass
class GraphSynchronizedEvent(GraphEvent):
    source_module: str = "knowledge_graph"
    sync_source_module: str = ""   # 'sensor', 'vision', 'incident', etc.
    nodes_created: int = 0
    nodes_updated: int = 0
    relationships_created: int = 0
    duration_ms: float = 0.0
    event_type: str = "GraphSynchronized"
    severity: str = "INFO"


# ── Versioning Events ──────────────────────────────────────────────────────────

@dataclass
class GraphVersionCreatedEvent(GraphEvent):
    node_id: str = ""
    node_label: str = ""
    version_number: int = 0
    snapshot_id: str = ""
    change_summary: str = ""
    event_type: str = "GraphVersionCreated"
    severity: str = "INFO"


# ── Analytics / Traversal Events ──────────────────────────────────────────────

@dataclass
class GraphTraversalCompletedEvent(GraphEvent):
    start_node_id: str = ""
    algorithm: str = ""
    nodes_visited: int = 0
    duration_ms: float = 0.0
    cache_hit: bool = False
    event_type: str = "GraphTraversalCompleted"
    severity: str = "INFO"


@dataclass
class GraphAnalyticsComputedEvent(GraphEvent):
    algorithm: str = ""
    entity_type: str | None = None
    result_count: int = 0
    duration_ms: float = 0.0
    cache_hit: bool = False
    event_type: str = "GraphAnalyticsComputed"
    severity: str = "INFO"


# ── Publisher Helpers ──────────────────────────────────────────────────────────

async def publish_graph_event(event: GraphEvent, topic: str) -> bool:
    """
    Publish a typed graph event through the Kafka EventBus.

    Automatically uses the most specific identifier as the partition key
    so that events for the same entity are ordered on the same partition.

    Returns True on success, False on failure (never raises).
    """
    try:
        from app.infrastructure.kafka.producer import EventBus
        payload = event.to_dict()
        # Derive partition key
        key: str | None = (
            getattr(event, "node_id", None)
            or getattr(event, "source_id", None)
            or event.event_id
        )
        return await EventBus.get().publish(topic=topic, payload=payload, key=key)
    except Exception as exc:
        log.error(f"Failed to publish graph event {type(event).__name__}: {exc}")
        return False


# ── Convenience publish functions ─────────────────────────────────────────────

async def publish_node_created(node_id: str, label: str, properties: dict[str, Any]) -> bool:
    event = NodeCreatedEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        node_id=node_id,
        label=label,
        properties=properties,
    )
    return await publish_graph_event(event, Topics.NODE_CREATED)


async def publish_node_updated(node_id: str, label: str, changes: dict[str, Any], version: int = 0) -> bool:
    event = NodeUpdatedEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        node_id=node_id,
        label=label,
        changes=changes,
        previous_version=version,
    )
    return await publish_graph_event(event, Topics.NODE_UPDATED)


async def publish_node_deleted(node_id: str, label: str, deleted_by: str = "system") -> bool:
    event = NodeDeletedEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        node_id=node_id,
        label=label,
        deleted_by=deleted_by,
    )
    return await publish_graph_event(event, Topics.NODE_DELETED)


async def publish_relationship_created(
    source_id: str,
    target_id: str,
    rel_type: str,
    properties: dict[str, Any] | None = None,
) -> bool:
    event = RelationshipCreatedEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        source_id=source_id,
        target_id=target_id,
        rel_type=rel_type,
        properties=properties or {},
    )
    return await publish_graph_event(event, Topics.RELATIONSHIP_CREATED)


async def publish_graph_synced(
    sync_source: str,
    nodes_created: int,
    nodes_updated: int,
    rels_created: int,
    duration_ms: float,
) -> bool:
    event = GraphSynchronizedEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        sync_source_module=sync_source,
        nodes_created=nodes_created,
        nodes_updated=nodes_updated,
        relationships_created=rels_created,
        duration_ms=duration_ms,
    )
    return await publish_graph_event(event, Topics.GRAPH_SYNCHRONIZED)
