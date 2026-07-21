"""
redis.py — Redis connection manager.

Public interface:
    get_client()    — returns the singleton Redis client
    check_health()  — returns True if Redis is reachable via PING
"""

import redis as redis_lib

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger("Redis")

_client: redis_lib.Redis | None = None


def get_client() -> redis_lib.Redis:
    """Return the singleton Redis client, creating it on first call."""
    global _client
    if _client is None:
        _client = redis_lib.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            password=settings.redis.password,
            db=settings.redis.db,
            decode_responses=True,
            socket_timeout=3,
            socket_connect_timeout=3,
        )
        log.info(f"Client created → {settings.redis.host}:{settings.redis.port}")
    return _client


def check_health() -> bool:
    """Return True if Redis responds to PING, False otherwise."""
    try:
        return bool(get_client().ping())
    except Exception as exc:
        log.error(f"Health check failed: {exc}")
        return False
