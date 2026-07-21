"""llm/health.py — LLM gateway health check."""

import time

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure import HealthStatus

log = get_logger("llm.health")


async def check_llm() -> HealthStatus:
    """
    Check LLM provider availability.

    Verifies the active provider has a configured API key.
    Does not make a real API call (avoids cost and latency).

    Returns:
        HealthStatus with service="llm", status, and optional error.
    """
    start = time.perf_counter()
    try:
        from app.infrastructure.llm.gateway import LLMGateway
        gateway = LLMGateway.get()
        available = await gateway._primary.is_available()
        latency_ms = int((time.perf_counter() - start) * 1000)
        if available:
            return HealthStatus(
                service="llm",
                status="healthy",
                latency_ms=latency_ms,
            )
        return HealthStatus(
            service="llm",
            status="unhealthy",
            latency_ms=latency_ms,
            error=f"Provider {settings.llm.provider!r} has no API key configured",
        )
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        log.warning(f"LLM health check failed: {exc}")
        return HealthStatus(
            service="llm",
            status="unhealthy",
            latency_ms=latency_ms,
            error=str(exc),
        )
