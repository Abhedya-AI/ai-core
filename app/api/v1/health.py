"""
app/api/v1/health.py — Kubernetes-ready health endpoints.

Three endpoints:
  GET /health/live     — liveness probe: is the process alive?
  GET /health/ready    — readiness probe: can it receive traffic?
  GET /health/startup  — startup probe: did initialization succeed?

Liveness:  lightweight — just returns 200. Kubernetes kills the pod if this fails.
Readiness: checks all infrastructure dependencies. Kubernetes stops routing if this fails.
Startup:   checks service registry. Kubernetes waits for this before enabling probes.
"""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Response

from app.core.logging import get_logger

router = APIRouter(tags=["health"])
log = get_logger("health")

_startup_time = datetime.now(tz=timezone.utc)


# ── GET /health/live ───────────────────────────────────────────────────────────

@router.get("/health/live", summary="Liveness probe")
async def health_live():
    """
    Liveness probe — Kubernetes uses this to detect dead pods.

    Returns 200 immediately if the process is alive.
    No infrastructure checks (those live in /health/ready).
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }


# ── GET /health/ready ──────────────────────────────────────────────────────────

@router.get("/health/ready", summary="Readiness probe")
async def health_ready(response: Response):
    """
    Readiness probe — Kubernetes uses this before routing traffic.

    Checks: PostgreSQL, Neo4j, Redis, Kafka, LLM.
    Returns 200 if all critical services are healthy.
    Returns 503 if any critical service is unhealthy.
    """
    from app.infrastructure.postgres.health import check_postgres
    from app.infrastructure.neo4j.health import check_neo4j
    from app.infrastructure.redis.health import check_redis
    from app.infrastructure.kafka.health import check_kafka
    from app.infrastructure.llm.health import check_llm

    # Run all checks concurrently
    results = await asyncio.gather(
        check_postgres(),
        check_neo4j(),
        check_redis(),
        check_kafka(),
        check_llm(),
        return_exceptions=True,
    )

    checks = []
    all_healthy = True

    for result in results:
        if isinstance(result, Exception):
            checks.append({
                "service": "unknown",
                "status": "unhealthy",
                "error": str(result),
            })
            all_healthy = False
        else:
            checks.append(result.to_dict())
            if not result.is_healthy:
                all_healthy = False

    status_code = 200 if all_healthy else 503
    response.status_code = status_code

    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "checks": checks,
    }


# ── GET /health/startup ────────────────────────────────────────────────────────

@router.get("/health/startup", summary="Startup probe")
async def health_startup(response: Response):
    """
    Startup probe — Kubernetes uses this during container boot.

    Checks that the service registry was populated successfully.
    Returns 200 once startup is complete.
    Returns 503 if still starting up or initialization failed.
    """
    from app.core.registry import registry

    status = registry.status()
    # Consider ready if at least Postgres and Redis registered
    critical_ready = status.get("postgres", False) or status.get("redis", False)

    if critical_ready:
        response.status_code = 200
        return {
            "status": "started",
            "uptime_seconds": (
                datetime.now(tz=timezone.utc) - _startup_time
            ).total_seconds(),
            "services": status,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }

    response.status_code = 503
    return {
        "status": "starting",
        "services": status,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }


# ── GET /api/v1/health (legacy) ───────────────────────────────────────────────

@router.get("/health", summary="Basic health check (legacy)")
async def health():
    """Legacy health endpoint kept for backward compatibility with existing tests."""
    from app.core.registry import registry
    status = registry.status()
    services = {
        "postgres": "healthy" if status.get("postgres") else "unhealthy",
        "neo4j": "healthy" if status.get("neo4j") else "unhealthy",
        "redis": "healthy" if status.get("redis") else "unhealthy",
    }
    is_degraded = any(v == "unhealthy" for v in services.values())
    return {
        "status": "degraded" if is_degraded else "healthy",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "services": services,
    }
