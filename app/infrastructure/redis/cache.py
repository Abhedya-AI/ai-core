"""
redis/cache.py — Generic CacheService.

A structured interface over Redis that GraphRAG, LLM, and Agent modules
will use. Prevents raw Redis commands from leaking into business logic.

Usage:
    from app.infrastructure.redis.cache import CacheService

    cache = CacheService(prefix="graphrag")
    await cache.set("query:abc123", result, ttl=300)
    value = await cache.get("query:abc123")
"""

import json
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.redis.client import get_client

log = get_logger("redis.cache")

_DEFAULT_TTL = 300  # 5 minutes


class CacheService:
    """
    Structured Redis cache with namespace prefixing.

    All keys are prefixed with `{prefix}:` to prevent collisions
    between different modules using the same Redis instance.

    Args:
        prefix: Namespace prefix. Examples: "graphrag", "llm", "session".
        default_ttl: Default TTL in seconds (default: 300).
    """

    def __init__(self, prefix: str, default_ttl: int = _DEFAULT_TTL) -> None:
        self._prefix = prefix
        self._default_ttl = default_ttl

    def _key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    async def get(self, key: str) -> Any | None:
        """Return the cached value, or None if not found / expired."""
        try:
            raw = await get_client().get(self._key(key))
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            log.warning(f"Cache get failed for {key!r}: {exc}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Cache a value with optional TTL.

        Args:
            key: Cache key (will be prefixed automatically).
            value: Any JSON-serialisable value.
            ttl: Time-to-live in seconds. Defaults to self.default_ttl.

        Returns:
            True if set successfully, False on error.
        """
        try:
            serialised = json.dumps(value)
            await get_client().setex(
                self._key(key),
                ttl or self._default_ttl,
                serialised,
            )
            return True
        except Exception as exc:
            log.warning(f"Cache set failed for {key!r}: {exc}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a cache key. Returns True if key existed."""
        try:
            deleted = await get_client().delete(self._key(key))
            return bool(deleted)
        except Exception as exc:
            log.warning(f"Cache delete failed for {key!r}: {exc}")
            return False

    async def exists(self, key: str) -> bool:
        """Return True if the key exists in the cache."""
        try:
            return bool(await get_client().exists(self._key(key)))
        except Exception as exc:
            log.warning(f"Cache exists check failed for {key!r}: {exc}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Reset the TTL on an existing key."""
        try:
            return bool(await get_client().expire(self._key(key), ttl))
        except Exception as exc:
            log.warning(f"Cache expire failed for {key!r}: {exc}")
            return False

    async def clear_prefix(self) -> int:
        """Delete all keys under this prefix. Returns number of deleted keys."""
        try:
            pattern = f"{self._prefix}:*"
            keys = await get_client().keys(pattern)
            if keys:
                return await get_client().delete(*keys)
            return 0
        except Exception as exc:
            log.warning(f"Cache clear_prefix failed for {self._prefix!r}: {exc}")
            return 0
