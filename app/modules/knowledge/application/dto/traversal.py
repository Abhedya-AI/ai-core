from typing import Any, Literal

from pydantic import BaseModel, Field


class TraversalRequest(BaseModel):
    """DTO for requesting multi-hop graph traversal."""

    start_node_id: str
    max_depth: int = Field(default=3, ge=1, le=10)
    relationship_types: list[str] = Field(default_factory=list)
    direction: Literal["OUTGOING", "INCOMING", "BOTH"] = "OUTGOING"
    target_labels: list[str] = Field(default_factory=list)


class TraversalPath(BaseModel):
    """Path result from a traversal."""

    nodes: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    depth: int


class TraversalResult(BaseModel):
    """Complete traversal response."""

    start_node_id: str
    paths: list[TraversalPath] = Field(default_factory=list)
    total_nodes_found: int = 0
