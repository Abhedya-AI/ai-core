"""
Neo4j connection manager.

Exposes:
    get_driver()    — returns the singleton Neo4j driver
    close_driver()  — cleanly closes the driver (called on shutdown)
    check_health()  — returns True if Neo4j is reachable
"""

from neo4j import GraphDatabase, Driver

from app.core.config.settings import database
from app.core.logger import get_logger

log = get_logger("Neo4j")

_driver: Driver | None = None


def get_driver() -> Driver:
    """Return the singleton Neo4j driver, creating it if necessary."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            database.neo4j_uri,
            auth=(database.neo4j_username, database.neo4j_password),
            connection_timeout=3,
        )
        log.info(f"Driver created → {database.neo4j_uri}")
    return _driver


def close_driver() -> None:
    """Close the Neo4j driver. Call this during application shutdown."""
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
