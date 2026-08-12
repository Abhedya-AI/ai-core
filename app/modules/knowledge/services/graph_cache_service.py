"""
services/graph_cache_service.py — Graph Redis Cache Service.

Uses the application Redis CacheService (app.infrastructure.redis.cache)
to cache frequent graph queries, traversals, neighborhoods, and analytics.

Cache TTL Strategy:
  - Node properties: 300s (5 min)
  - Subgraph / Neighborhood: 120s (2 min)
  - Shortest Path: 120s (2 min)
  - Analytics (PageRank, Centrality): 600s (10 min)
  - Context window: 180s (3 min)

Key Namespacing:
  - graph:node:{id}
  - graph:neighborhood:{id}:{hops}
  - graph:path:{start}:{target}
  - graph:analytics:{alg}:{type}
  - graph:context:{id}:{depth}
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.redis.cache import CacheService

log = get_logger("knowledge.service.cache")

_GRAPH_CACHE_PREFIX = "graph"


class GraphCacheService:
    """Redis cache manager for Knowledge Graph queries and computations."""

    def __init__(self, cache: CacheService | None = None) -> None:
        self._cache = cache or CacheService(prefix=_GRAPH_CACHE_PREFIX, default_ttl=300)

    # ── Node Cache ────────────────────────────────────────────────────────────

    async def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get cached node dict by node_id."""
        return await self._cache.get(f"node:{node_id}")

    async def set_node(self, node_id: str, data: dict[str, Any], ttl: int = 300) -> bool:
        """Cache node dict."""
        return await self._cache.set(f"node:{node_id}", data, ttl=ttl)

    async def invalidate_node(self, node_id: str) -> bool:
        """Invalidate cached node."""
        return await self._cache.delete(f"node:{node_id}")

    # ── Neighborhood Cache ────────────────────────────────────────────────────

    async def get_neighborhood(self, node_id: str, hops: int) -> dict[str, Any] | None:
        """Get cached neighborhood dict."""
        return await self._cache.get(f"neighborhood:{node_id}:{hops}")

    async def set_neighborhood(
        self, node_id: str, hops: int, data: dict[str, Any], ttl: int = 120
    ) -> bool:
        """Cache neighborhood dict."""
        return await self._cache.set(f"neighborhood:{node_id}:{hops}", data, ttl=ttl)

    # ── Path Cache ────────────────────────────────────────────────────────────

    async def get_shortest_path(self, start_id: str, target_id: str) -> dict[str, Any] | None:
        """Get cached shortest path."""
        return await self._cache.get(f"path:{start_id}:{target_id}")

    async def set_shortest_path(
        self, start_id: str, target_id: str, data: dict[str, Any], ttl: int = 120
    ) -> bool:
        """Cache shortest path."""
        return await self._cache.set(f"path:{start_id}:{target_id}", data, ttl=ttl)

    # ── Analytics Cache ───────────────────────────────────────────────────────

    async def get_analytics(self, algorithm: str, entity_type: str | None = None) -> dict[str, Any] | None:
        """Get cached analytics result."""
        key = f"analytics:{algorithm}:{entity_type or 'all'}"
        return await self._cache.get(key)

    async def set_analytics(
        self,
        algorithm: str,
        entity_type: str | None,
        data: dict[str, Any],
        ttl: int = 600,
    ) -> bool:
        """Cache analytics result."""
        key = f"analytics:{algorithm}:{entity_type or 'all'}"
        return await self._cache.set(key, data, ttl=ttl)

    # ── Context Cache ─────────────────────────────────────────────────────────

    async def get_context(self, node_id: str, depth: int) -> dict[str, Any] | None:
        """Get cached GraphContext dict."""
        return await self._cache.get(f"context:{node_id}:{depth}")

    async def set_context(
        self, node_id: str, depth: int, data: dict[str, Any], ttl: int = 180
    ) -> bool:
        """Cache GraphContext dict."""
        return await self._cache.set(f"context:{node_id}:{depth}", data, ttl=ttl)

    # ── Invalidation ──────────────────────────────────────────────────────────

    async def invalidate_all(self) -> int:
        """Clear all graph cache keys."""
        count = await self._cache.clear_prefix()
        log.info(f"Invalidated {count} graph cache keys")
        return count
