"""
dto/search_dto.py — DTOs for Knowledge Graph Search.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request to search the Knowledge Graph."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    entity_types: list[str] = Field(
        default_factory=list,
        description="Filter results by entity type labels (empty = search all)",
    )
    search_type: str = Field(
        default="text",
        description="Search strategy: text | property | structural | proximity",
    )
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional property filters (equality)",
    )
    proximity_node_id: str | None = Field(
        default=None,
        description="For proximity search: center node ID",
    )
    proximity_hops: int = Field(
        default=2,
        ge=1,
        le=5,
        description="For proximity search: max hops from center",
    )
    case_sensitive: bool = Field(default=False)


class SearchHit(BaseModel):
    """A single search result."""

    node_id: str
    label: str
    name: str | None = None
    code: str | None = None
    score: float = Field(default=1.0, description="Relevance score (0-1)")
    matched_properties: dict[str, Any] = Field(default_factory=dict)
    snippet: str | None = Field(default=None, description="Short text excerpt showing the match")


class SearchResult(BaseModel):
    """Paginated search result set."""

    query: str
    total: int
    offset: int
    limit: int
    hits: list[SearchHit]
    execution_time_ms: float
    search_type: str
    cache_hit: bool = False
