"""neo4j/health.py — Neo4j health check."""

import time

from app.core.logging import get_logger
from app.infrastructure import HealthStatus
from app.infrastructure.neo4j.session import get_neo4j_session

log = get_logger("neo4j.health")


async def check_neo4j() -> HealthStatus:
    """
    Check Neo4j connectivity via RETURN 1.

    Returns:
        HealthStatus with service="neo4j", latency, and optional error.
    """
    start = time.perf_counter()
    try:
        async with get_neo4j_session() as session:
            result = await session.run("RETURN 1 AS ok")
            await result.consume()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return HealthStatus(service="neo4j", status="healthy", latency_ms=latency_ms)
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        log.warning(f"Neo4j health check failed: {exc}")
        return HealthStatus(
            service="neo4j",
            status="unhealthy",
            latency_ms=latency_ms,
            error=str(exc),
        )
