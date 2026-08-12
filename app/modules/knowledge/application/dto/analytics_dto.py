"""
dto/analytics_dto.py — DTOs for Graph Analytics Operations.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyticsRequest(BaseModel):
    """Request to compute a graph analytics algorithm."""

    algorithm: str = Field(
        ...,
        description="Algorithm: pagerank | degree | in_degree | out_degree | betweenness | community | impact | similarity",
    )
    entity_type: str | None = Field(default=None, description="Filter by entity type label")
    node_id: str | None = Field(default=None, description="Seed node ID for local analytics")
    target_node_id: str | None = Field(default=None, description="Target node for similarity/path algorithms")
    direction: str = Field(default="downstream", description="impact direction: downstream | upstream")
    max_iterations: int = Field(default=20, ge=1, le=100)
    damping_factor: float = Field(default=0.85, ge=0.1, le=1.0)
    max_depth: int = Field(default=5, ge=1, le=10)
    limit: int = Field(default=50, ge=1, le=500)


class NodeScore(BaseModel):
    """A single node with its computed algorithm score."""

    node_id: str
    label: str
    name: str | None = None
    score: float
    rank: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class CentralityResult(BaseModel):
    """Result of a centrality algorithm (degree, pagerank, etc.)."""

    algorithm: str
    entity_type: str | None
    total_nodes: int
    results: list[NodeScore]
    execution_time_ms: float


class CommunityMember(BaseModel):
    """A node belonging to a detected community."""

    node_id: str
    label: str
    name: str | None = None
    community_id: int


class CommunityResult(BaseModel):
    """Result of community detection."""

    total_communities: int
    total_nodes: int
    communities: dict[int, list[CommunityMember]]
    largest_community_size: int = 0
    execution_time_ms: float


class ImpactNode(BaseModel):
    """A node affected by a cascading impact analysis."""

    node_id: str
    label: str
    name: str | None = None
    distance: int
    path: list[str] = Field(default_factory=list)
    risk_level: str | None = None
    severity: str | None = None


class ImpactAnalysisResult(BaseModel):
    """Result of downstream/upstream impact analysis."""

    source_id: str
    direction: str
    max_depth: int
    total_affected: int
    affected_nodes: list[ImpactNode]
    execution_time_ms: float


class SimilarityResult(BaseModel):
    """Similarity score between two nodes."""

    node_id_a: str
    node_id_b: str
    jaccard_score: float
    common_neighbors: int
    common_neighbor_ids: list[str] = Field(default_factory=list)


class AnalyticsResult(BaseModel):
    """Unified analytics response envelope."""

    algorithm: str
    entity_type: str | None = None
    centrality: CentralityResult | None = None
    community: CommunityResult | None = None
    impact: ImpactAnalysisResult | None = None
    similarity: SimilarityResult | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    cache_hit: bool = False
