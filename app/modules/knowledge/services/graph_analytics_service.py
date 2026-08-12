"""
services/graph_analytics_service.py — Graph Analytics Facade Service.

Orchestrates graph centrality, PageRank, community detection, impact analysis,
and similarity algorithms across AnalyticsRepository, TraversalRepository,
and GraphIntelligenceEngine with Redis cache integration.
"""
from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.analytics_dto import (
    AnalyticsRequest,
    AnalyticsResult,
    CentralityResult,
    CommunityResult,
    ImpactAnalysisResult,
    ImpactNode,
    NodeScore,
    SimilarityResult,
)
from app.modules.knowledge.infrastructure.repositories.analytics_repository import (
    AnalyticsRepository,
)
from app.modules.knowledge.infrastructure.repositories.traversal_repository import (
    TraversalRepository,
)
from app.modules.knowledge.services.graph_cache_service import GraphCacheService

log = get_logger("knowledge.service.analytics")


class GraphAnalyticsService:
    """Facade service for graph analytics algorithms with caching."""

    def __init__(
        self,
        analytics_repo: AnalyticsRepository | None = None,
        traversal_repo: TraversalRepository | None = None,
        cache_service: GraphCacheService | None = None,
    ) -> None:
        self._analytics = analytics_repo or AnalyticsRepository()
        self._traversal = traversal_repo or TraversalRepository()
        self._cache = cache_service or GraphCacheService()

    async def run_analytics(self, request: AnalyticsRequest) -> AnalyticsResult:
        """Run requested analytics algorithm and return standardized result envelope."""
        t0 = time.monotonic()
        alg = request.algorithm.lower()

        # Check cache for centrality/community
        cached = await self._cache.get_analytics(alg, request.entity_type)
        if cached:
            log.info(f"Analytics cache hit for algorithm={alg}")
            return AnalyticsResult(
                algorithm=alg,
                entity_type=request.entity_type,
                raw_data=cached,
                execution_time_ms=0.0,
                cache_hit=True,
            )

        result = AnalyticsResult(algorithm=alg, entity_type=request.entity_type)

        if alg in ("degree", "in_degree", "out_degree"):
            centrality = await self.compute_degree_centrality(
                label=request.entity_type,
                direction=alg,
                limit=request.limit,
            )
            result.centrality = centrality

        elif alg == "pagerank":
            centrality = await self.compute_pagerank(
                label=request.entity_type,
                iterations=request.max_iterations,
                damping=request.damping_factor,
                limit=request.limit,
            )
            result.centrality = centrality

        elif alg == "community":
            community = await self.detect_communities(
                label=request.entity_type,
                limit=request.limit,
            )
            result.community = community

        elif alg == "impact" and request.node_id:
            impact = await self.analyze_impact(
                node_id=request.node_id,
                direction=request.direction,
                max_depth=request.max_depth,
                limit=request.limit,
            )
            result.impact = impact

        elif alg == "similarity" and request.node_id and request.target_node_id:
            sim = await self.compute_similarity(
                node_id_a=request.node_id,
                node_id_b=request.target_node_id,
            )
            result.similarity = sim

        else:
            # Subgraph stats fallback
            stats = await self._analytics.subgraph_stats(
                entity_types=[request.entity_type] if request.entity_type else None
            )
            result.raw_data = stats

        elapsed = (time.monotonic() - t0) * 1000
        result.execution_time_ms = elapsed

        # Cache result
        if result.centrality or result.community:
            cache_payload = result.model_dump()
            await self._cache.set_analytics(alg, request.entity_type, cache_payload, ttl=600)

        log.info(f"Ran analytics algorithm={alg} in {elapsed:.1f}ms")
        return result

    async def compute_degree_centrality(
        self,
        label: str | None = None,
        direction: str = "degree",
        limit: int = 50,
    ) -> CentralityResult:
        """Compute degree centrality ranking."""
        t0 = time.monotonic()
        if direction == "in_degree":
            raw = await self._analytics.in_degree_centrality(label=label, limit=limit)
        elif direction == "out_degree":
            raw = await self._analytics.out_degree_centrality(label=label, limit=limit)
        else:
            raw = await self._analytics.degree_centrality(label=label, limit=limit)

        scores = [
            NodeScore(
                node_id=item["node_id"],
                label=item.get("label", ""),
                name=item.get("name"),
                score=item["score"],
                rank=item["rank"],
            )
            for item in raw
        ]
        elapsed = (time.monotonic() - t0) * 1000

        return CentralityResult(
            algorithm=f"centrality_{direction}",
            entity_type=label,
            total_nodes=len(scores),
            results=scores,
            execution_time_ms=elapsed,
        )

    async def compute_pagerank(
        self,
        label: str | None = None,
        iterations: int = 20,
        damping: float = 0.85,
        limit: int = 50,
    ) -> CentralityResult:
        """Compute approximate PageRank centrality."""
        t0 = time.monotonic()
        raw = await self._analytics.pagerank_in_memory(
            label=label, iterations=iterations, damping=damping, limit=limit
        )
        scores = [
            NodeScore(
                node_id=item["node_id"],
                label=item.get("label", ""),
                name=item.get("name"),
                score=item["score"],
                rank=item["rank"],
            )
            for item in raw
        ]
        elapsed = (time.monotonic() - t0) * 1000

        return CentralityResult(
            algorithm="pagerank",
            entity_type=label,
            total_nodes=len(scores),
            results=scores,
            execution_time_ms=elapsed,
        )

    async def detect_communities(
        self,
        label: str | None = None,
        limit: int = 200,
    ) -> CommunityResult:
        """Detect communities using label propagation."""
        t0 = time.monotonic()
        raw = await self._analytics.community_detection(label=label, limit=limit)
        elapsed = (time.monotonic() - t0) * 1000

        return CommunityResult(
            total_communities=raw.get("total_communities", 0),
            total_nodes=raw.get("total_nodes", 0),
            largest_community_size=raw.get("largest_community_size", 0),
            communities=raw.get("communities", {}),
            execution_time_ms=elapsed,
        )

    async def analyze_impact(
        self,
        node_id: str,
        direction: str = "downstream",
        max_depth: int = 5,
        limit: int = 100,
    ) -> ImpactAnalysisResult:
        """Analyze cascading risk impact upstream or downstream."""
        t0 = time.monotonic()
        raw = await self._traversal.impact_analysis(
            node_id=node_id,
            max_depth=max_depth,
            direction="OUTGOING" if direction == "downstream" else "INCOMING",
            limit=limit,
        )

        affected = [
            ImpactNode(
                node_id=item["node"].get("id", ""),
                label=item.get("entity_type", ""),
                name=item["node"].get("name") or item["node"].get("title"),
                distance=item.get("distance", 0),
                path=item.get("path_ids", []),
                risk_level=item["node"].get("risk_level"),
                severity=item["node"].get("severity"),
            )
            for item in raw
        ]
        elapsed = (time.monotonic() - t0) * 1000

        return ImpactAnalysisResult(
            source_id=node_id,
            direction=direction,
            max_depth=max_depth,
            total_affected=len(affected),
            affected_nodes=affected,
            execution_time_ms=elapsed,
        )

    async def compute_similarity(self, node_id_a: str, node_id_b: str) -> SimilarityResult:
        """Compute Jaccard graph similarity between two nodes."""
        raw = await self._analytics.node_similarity(node_id_a, node_id_b)
        return SimilarityResult(**raw)
