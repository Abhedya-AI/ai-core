"""
dto/sync_dto.py — DTOs for Graph Synchronization Operations.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SyncRelationship(BaseModel):
    """A relationship to create as part of a node sync operation."""

    target_id: str
    rel_type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class SyncNodeRequest(BaseModel):
    """Request to upsert a single node into the Knowledge Graph."""

    source_module: str = Field(..., description="Source module: sensor | vision | incident | workflow")
    node_id: str = Field(..., description="Stable ID (e.g., sensor UUID, incident UUID)")
    label: str = Field(..., description="Neo4j label: Sensor | Equipment | Incident | Detection | etc.")
    properties: dict[str, Any] = Field(..., description="Node properties to set/update")
    relationships: list[SyncRelationship] = Field(
        default_factory=list,
        description="Relationships to create from this node to other existing nodes",
    )
    create_snapshot: bool = Field(
        default=False,
        description="Whether to snapshot the node before updating it",
    )


class SyncBatchRequest(BaseModel):
    """Request to sync multiple nodes in a single transaction."""

    source_module: str
    nodes: list[SyncNodeRequest]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transaction: bool = Field(
        default=False,
        description="Run as single Neo4j transaction (all-or-nothing)",
    )


class SyncResult(BaseModel):
    """Result of a sync operation."""

    source_module: str
    nodes_created: int = 0
    nodes_updated: int = 0
    relationships_created: int = 0
    errors: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    success: bool = True

    @property
    def total_changes(self) -> int:
        return self.nodes_created + self.nodes_updated + self.relationships_created


class SyncEvent(BaseModel):
    """An incoming event that triggers a sync operation."""

    event_type: str = Field(..., description="sensor_reading | vision_detection | incident_created | etc.")
    entity_id: str
    entity_type: str
    payload: dict[str, Any]
    source_module: str
    timestamp: str
    priority: str = Field(default="normal", description="normal | high | critical")
