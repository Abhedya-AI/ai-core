"""cache.py — Redis caching layer for GraphRAG."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.redis.cache import CacheService

log = get_logger("graphrag.retrieval.cache")


class GraphRAGCache:
    """Redis cache for query embeddings, graph subgraphs, and GraphRAG answers."""

    def __init__(self, cache_service: CacheService | None = None) -> None:
        self._cache = cache_service or CacheService(prefix="graphrag")

    async def get_cached_response(self, query_key: str) -> dict[str, Any] | None:
        """Fetch cached response for a query."""
        return await self._cache.get(query_key)

    async def cache_response(self, query_key: str, data: dict[str, Any], ttl: int = 300) -> bool:
        """Cache response data with a short TTL (default 5 mins)."""
        return await self._cache.set(query_key, data, ttl=ttl)
