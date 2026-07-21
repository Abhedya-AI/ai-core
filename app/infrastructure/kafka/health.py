"""kafka/health.py — Kafka health check."""

import time

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure import HealthStatus

log = get_logger("kafka.health")


async def check_kafka() -> HealthStatus:
    """
    Check Kafka broker connectivity.

    When KAFKA_ENABLED=False, returns healthy immediately (Kafka not in use).
    When enabled, attempts a real broker connection.

    Returns:
        HealthStatus with service="kafka", latency, and optional error.
    """
    if not settings.kafka.enabled:
        return HealthStatus(service="kafka", status="healthy", latency_ms=0)

    start = time.perf_counter()
    try:
        from aiokafka.admin import AIOKafkaAdminClient
        admin = AIOKafkaAdminClient(
            bootstrap_servers=settings.kafka.bootstrap_servers,
            client_id=f"{settings.kafka.client_id}-health",
            request_timeout_ms=3000,
        )
        await admin.start()
        await admin.close()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return HealthStatus(service="kafka", status="healthy", latency_ms=latency_ms)
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        log.warning(f"Kafka health check failed: {exc}")
        return HealthStatus(
            service="kafka",
            status="unhealthy",
            latency_ms=latency_ms,
            error=str(exc),
        )
