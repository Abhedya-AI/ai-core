"""
use_cases/traversal_use_cases.py — Traversal Use Cases.

Implements Clean Architecture use cases for multi-hop graph traversal,
shortest path discovery, and neighborhood extraction.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.traversal import (
    TraversalRequest,
    TraversalResult,
)
from app.modules.knowledge.infrastructure.repositories.traversal_repository import (
    TraversalRepository,
)
from app.modules.knowledge.services.graph_cache_service import GraphCacheService

log = get_logger("knowledge.use_case.traversal")


class TraverseGraphUseCase:
    """Use case: Multi-hop graph traversal from a start node."""

    def __init__(self, repo: TraversalRepository | None = None) -> None:
        self._repo = repo or TraversalRepository()

    async def execute(self, request: TraversalRequest) -> TraversalResult:
        """Execute traversal query via repository."""
        return await self._repo.traverse(request)


class ShortestPathUseCase:
    """Use case: Shortest path calculation between source and target nodes with caching."""

    def __init__(
        self,
        repo: TraversalRepository | None = None,
        cache: GraphCacheService | None = None,
    ) -> None:
        self._repo = repo or TraversalRepository()
        self._cache = cache or GraphCacheService()

    async def execute(self, start_node_id: str, target_node_id: str) -> dict[str, Any] | None:
        """Calculate shortest path, checking Redis cache first."""
        cached = await self._cache.get_shortest_path(start_node_id, target_node_id)
        if cached:
            return cached

        path = await self._repo.shortest_path(start_node_id, target_node_id)
        if path:
            await self._cache.set_shortest_path(start_node_id, target_node_id, path)

        return path


class NeighborhoodUseCase:
    """Use case: Extract k-hop neighborhood graph ({nodes, edges}) for visual rendering."""

    def __init__(
        self,
        repo: TraversalRepository | None = None,
        cache: GraphCacheService | None = None,
    ) -> None:
        self._repo = repo or TraversalRepository()
        self._cache = cache or GraphCacheService()

    async def execute(self, node_id: str, hops: int = 2, limit: int = 200) -> dict[str, Any]:
        """Extract neighborhood, checking Redis cache first."""
        cached = await self._cache.get_neighborhood(node_id, hops)
        if cached:
            return cached

        nb_data = await self._repo.get_neighborhood(node_id=node_id, hops=hops, limit=limit)
        if nb_data and nb_data.get("nodes"):
            await self._cache.set_neighborhood(node_id, hops, nb_data)

        return nb_data
