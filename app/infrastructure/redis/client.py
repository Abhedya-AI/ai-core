"""
redis/client.py — Async Redis client singleton.

Redis is used for:
  - GraphRAG result cache
  - LLM response cache
  - Agent state storage
  - Session management
  - Rate limiting

Build the generic client here. Specific use cases live in cache.py.
"""

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("redis.client")

_pool: ConnectionPool | None = None
_client: Redis | None = None


def _build_url() -> str:
    r = settings.redis
    if r.password:
        return f"redis://:{r.password}@{r.host}:{r.port}/{r.db}"
    return f"redis://{r.host}:{r.port}/{r.db}"


def get_client() -> Redis:
    """
    Return the async Redis client singleton.

    Uses a connection pool internally. Safe to call from any coroutine.
    The pool is shared across all consumers in the process.
    """
    global _pool, _client
    if _client is None:
        _pool = aioredis.ConnectionPool.from_url(
            _build_url(),
            max_connections=20,
            socket_timeout=3,
            socket_connect_timeout=3,
            decode_responses=True,
        )
        _client = aioredis.Redis(connection_pool=_pool)
        log.info(
            f"Redis client created → {settings.redis.host}:{settings.redis.port}"
        )
    return _client


async def close_client() -> None:
    """Close the Redis connection pool."""
    global _pool, _client
    if _client is not None:
        await _client.aclose()
        _client = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None
        log.info("Redis connection pool closed")
