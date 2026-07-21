"""postgres/health.py — PostgreSQL health check."""

import time

from sqlalchemy import text

from app.core.logging import get_logger
from app.infrastructure import HealthStatus
from app.infrastructure.postgres.engine import get_engine

log = get_logger("postgres.health")


async def check_postgres() -> HealthStatus:
    """
    Check PostgreSQL connectivity by executing SELECT 1.

    Returns:
        HealthStatus with service="postgres", status="healthy"|"unhealthy",
        latency_ms, and optional error message.
    """
    start = time.perf_counter()
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = int((time.perf_counter() - start) * 1000)
        return HealthStatus(service="postgres", status="healthy", latency_ms=latency_ms)
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        log.warning(f"PostgreSQL health check failed: {exc}")
        return HealthStatus(
            service="postgres",
            status="unhealthy",
            latency_ms=latency_ms,
            error=str(exc),
        )
