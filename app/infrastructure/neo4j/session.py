"""
neo4j/session.py — Neo4j async session context manager.

Provides a convenient get_session() context manager so callers
never touch the driver directly.

Usage:
    from app.infrastructure.neo4j.session import get_neo4j_session

    async with get_neo4j_session() as session:
        result = await session.run("MATCH (n) RETURN count(n) AS count")
        record = await result.single()
        return record["count"]
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from neo4j import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.neo4j.driver import get_driver

log = get_logger("neo4j.session")


@asynccontextmanager
async def get_neo4j_session(
    database: str = "neo4j",
) -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that yields a Neo4j session.

    Args:
        database: Neo4j database name (default: "neo4j").
                  Use "system" for administrative commands.

    Example:
        async with get_neo4j_session() as session:
            await session.run("CREATE (n:Node {name: $name})", name="A")
    """
    driver = await get_driver()
    async with driver.session(database=database) as session:
        yield session
