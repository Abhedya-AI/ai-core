"""
neo4j.py — Neo4j graph database connection manager.

Public interface:
    get_driver()    — returns the singleton Neo4j driver
    close_driver()  — cleanly closes the driver (call on shutdown)
    check_health()  — returns True if Neo4j is reachable
"""

from neo4j import GraphDatabase, Driver

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger("Neo4j")

_driver: Driver | None = None


def get_driver() -> Driver:
    """Return the singleton Neo4j driver, creating it on first call."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.username, settings.neo4j.password),
            max_connection_pool_size=settings.neo4j.max_connection_pool_size,
            connection_timeout=settings.neo4j.connection_timeout,
        )
        log.info(f"Driver created → {settings.neo4j.uri}")
    return _driver


def close_driver() -> None:
    """Close the Neo4j driver. Call during application shutdown."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        log.info("Driver closed")


def check_health() -> bool:
    """Return True if Neo4j is reachable, False otherwise."""
    try:
        get_driver().verify_connectivity()
        return True
    except Exception as exc:
        log.error(f"Health check failed: {exc}")
        return False
