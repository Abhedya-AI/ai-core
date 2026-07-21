"""redis/health.py — Redis health check."""

import time

from app.core.logging import get_logger
from app.infrastructure import HealthStatus
from app.infrastructure.redis.client import get_client

log = get_logger("redis.health")


async def check_redis() -> HealthStatus:
    """
    Check Redis connectivity via PING.

    Returns:
        HealthStatus with service="redis", latency, and optional error.
    """
    start = time.perf_counter()
    try:
        response = await get_client().ping()
        latency_ms = int((time.perf_counter() - start) * 1000)
        if response:
            return HealthStatus(service="redis", status="healthy", latency_ms=latency_ms)
        return HealthStatus(
            service="redis",
            status="unhealthy",
            latency_ms=latency_ms,
            error="PING returned False",
        )
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        log.warning(f"Redis health check failed: {exc}")
        return HealthStatus(
            service="redis",
            status="unhealthy",
            latency_ms=latency_ms,
            error=str(exc),
        )
