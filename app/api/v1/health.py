"""
Health check endpoint.

GET /health
GET /api/v1/health

Checks PostgreSQL, Neo4j, and Redis connectivity in parallel using a thread
pool so blocking driver calls never stall the async event loop.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter

import app.database.postgres as pg
import app.database.neo4j as neo
import app.database.redis as rds

router = APIRouter(tags=["Health"])

_executor = ThreadPoolExecutor(max_workers=3)


async def _run(fn) -> bool:
    """Execute a blocking health-check function in a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, fn)


@router.get("/health", summary="Platform health check")
async def health():
    """
    Verify connectivity to all platform dependencies.

    Returns individual status for each service along with overall platform health.
    """
    postgres_ok, neo4j_ok, redis_ok = await asyncio.gather(
        _run(pg.check_health),
        _run(neo.check_health),
        _run(rds.check_health),
    )

    def status(ok: bool) -> str:
        return "connected" if ok else "disconnected"

    all_healthy = postgres_ok and neo4j_ok and redis_ok

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": {
            "postgres": status(postgres_ok),
            "neo4j":    status(neo4j_ok),
            "redis":    status(redis_ok),
        },
    }
