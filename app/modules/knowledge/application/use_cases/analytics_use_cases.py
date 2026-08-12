"""
use_cases/analytics_use_cases.py — Analytics Use Cases.

Implements Clean Architecture use cases for graph algorithms:
centrality, PageRank, community detection, impact analysis, and similarity.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.analytics_dto import (
    AnalyticsRequest,
    AnalyticsResult,
    CentralityResult,
    CommunityResult,
    ImpactAnalysisResult,
)
from app.modules.knowledge.services.graph_analytics_service import GraphAnalyticsService

log = get_logger("knowledge.use_case.analytics")


class ComputeAnalyticsUseCase:
    """Use case: Execute graph analytics algorithm via GraphAnalyticsService."""

    def __init__(self, service: GraphAnalyticsService | None = None) -> None:
        self._service = service or GraphAnalyticsService()

    async def execute(self, request: AnalyticsRequest) -> AnalyticsResult:
        """Run requested analytics algorithm."""
        return await self._service.run_analytics(request)


class ComputeCentralityUseCase:
    """Use case: Compute degree or PageRank centrality."""

    def __init__(self, service: GraphAnalyticsService | None = None) -> None:
        self._service = service or GraphAnalyticsService()

    async def execute(
        self,
        label: str | None = None,
        algorithm: str = "degree",
        limit: int = 50,
    ) -> CentralityResult:
        """Compute centrality ranking."""
        if algorithm == "pagerank":
            return await self._service.compute_pagerank(label=label, limit=limit)
        return await self._service.compute_degree_centrality(label=label, direction=algorithm, limit=limit)


class DetectCommunitiesUseCase:
    """Use case: Detect graph communities using label propagation."""

    def __init__(self, service: GraphAnalyticsService | None = None) -> None:
        self._service = service or GraphAnalyticsService()

    async def execute(self, label: str | None = None, limit: int = 200) -> CommunityResult:
        """Detect communities."""
        return await self._service.detect_communities(label=label, limit=limit)


class AnalyzeImpactUseCase:
    """Use case: Upstream or downstream cascading risk impact analysis."""

    def __init__(self, service: GraphAnalyticsService | None = None) -> None:
        self._service = service or GraphAnalyticsService()

    async def execute(
        self,
        node_id: str,
        direction: str = "downstream",
        max_depth: int = 5,
        limit: int = 100,
    ) -> ImpactAnalysisResult:
        """Analyze cascading impact."""
        return await self._service.analyze_impact(
            node_id=node_id, direction=direction, max_depth=max_depth, limit=limit
        )
