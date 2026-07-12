"""
Redis connection manager.

Exposes:
    get_client()    — returns the singleton Redis client
    check_health()  — returns True if Redis is reachable
"""

import redis

from app.core.config.settings import database
from app.core.logger import get_logger

log = get_logger("Redis")

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    """Return the singleton Redis client, creating it if necessary."""
    global _client
    if _client is None:
        _client = redis.Redis(
            host=database.redis_host,
            port=database.redis_port,
            password=database.redis_password,
            decode_responses=True,
            socket_timeout=3,
            socket_connect_timeout=3,
        )
        log.info(f"Client created → {database.redis_host}:{database.redis_port}")
    return _client


def check_health() -> bool:
    """Return True if Redis is reachable via PING, False otherwise."""
    try:
        return bool(get_client().ping())
    except Exception as exc:
        log.error(f"Health check failed: {exc}")
        return False
