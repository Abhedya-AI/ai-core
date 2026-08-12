"""
api/schemas.py — Pydantic Request & Response Schemas for Knowledge API.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.modules.knowledge.application.dto.analytics_dto import (
    AnalyticsRequest,
    AnalyticsResult,
)
from app.modules.knowledge.application.dto.context_dto import (
    ContextRequest,
    GraphContext,
)
from app.modules.knowledge.application.dto.create_node import CreateNodeRequest
from app.modules.knowledge.application.dto.graph_query import CreateRelationshipRequest
from app.modules.knowledge.application.dto.history_dto import (
    HistoryRequest,
    HistoryResult,
    RestoreRequest,
)
from app.modules.knowledge.application.dto.search_dto import (
    SearchRequest,
    SearchResult,
)
from app.modules.knowledge.application.dto.sync_dto import (
    SyncBatchRequest,
    SyncNodeRequest,
    SyncResult,
)
from app.modules.knowledge.application.dto.traversal import (
    TraversalRequest,
    TraversalResult,
)
from app.modules.knowledge.application.dto.update_node import UpdateNodeRequest


class NodeResponse(BaseModel):
    """Response containing node details."""

    id: str
    label: str
    properties: dict[str, Any]


class RelationshipResponse(BaseModel):
    """Response for a relationship operation."""

    source_id: str
    target_id: str
    rel_type: str
    properties: dict[str, Any] = Field(default_factory=dict)
    success: bool = True


class VisualGraphResponse(BaseModel):
    """Response format for UI visual network components ({nodes, edges})."""

    center_node_id: str | None = None
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    total_nodes: int = 0
    total_edges: int = 0


__all__ = [
    "CreateNodeRequest",
    "UpdateNodeRequest",
    "CreateRelationshipRequest",
    "TraversalRequest",
    "TraversalResult",
    "AnalyticsRequest",
    "AnalyticsResult",
    "ContextRequest",
    "GraphContext",
    "SyncNodeRequest",
    "SyncBatchRequest",
    "SyncResult",
    "SearchRequest",
    "SearchResult",
    "HistoryRequest",
    "HistoryResult",
    "RestoreRequest",
    "NodeResponse",
    "RelationshipResponse",
    "VisualGraphResponse",
]
