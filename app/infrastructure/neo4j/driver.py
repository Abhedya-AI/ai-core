"""
neo4j/driver.py — Neo4j async driver singleton.

No Cypher. No graph queries. No nodes. Only connectivity.

The driver is created once per process and shared across all consumers.
Creating multiple drivers is wasteful and causes connection pool exhaustion.
"""

from neo4j import AsyncDriver, AsyncGraphDatabase, Auth, basic_auth

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("neo4j.driver")

_driver: AsyncDriver | None = None


def _build_auth() -> Auth:
    return basic_auth(settings.neo4j.username, settings.neo4j.password)


async def get_driver() -> AsyncDriver:
    """
    Return the async Neo4j driver singleton, creating it on first call.

    Uses bolt:// by default (neo4j+s:// for encrypted cloud connections).
    """
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j.uri,
            auth=_build_auth(),
            max_connection_pool_size=50,
            connection_timeout=10,
        )
        log.info(f"Neo4j async driver created → {settings.neo4j.uri}")
    return _driver


async def close_driver() -> None:
    """Close the driver and all pooled connections."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        log.info("Neo4j driver closed")
