"""
app/core/lifespan.py — FastAPI application lifespan manager.

Full startup/shutdown sequence:

Startup:
  1. Logging          — must be first
  2. PostgreSQL       — async engine + connectivity check
  3. Neo4j            — async driver + connectivity check
  4. Redis            — connection pool + connectivity check
  5. Kafka EventBus   — producer (no-op if disabled)
  6. LLM Gateway      — provider init
  7. Service Registry — register all clients
  ✓ Application ready

Shutdown (reverse order):
  1. Kafka EventBus   — flush and close producer
  2. Neo4j            — close driver
  3. PostgreSQL       — dispose engine
  4. Redis            — close connection pool
  5. Logging          — flush file handlers last
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import configure_logging, get_logger
from app.core.logging.logger import shutdown_logging

# Logging must be configured before any logger is created
configure_logging()

log = get_logger("abhedya.lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager."""

    # ═══════════════════════════════════════════════════════════════════════════
    # STARTUP
    # ═══════════════════════════════════════════════════════════════════════════
    log.info("═" * 60)
    log.info("ABHEDYA AI Core — Starting up")
    log.info("═" * 60)

    from app.core.registry import registry

    # ── 1. PostgreSQL ──────────────────────────────────────────────────────────
    try:
        from app.infrastructure.postgres.engine import get_engine
        from app.infrastructure.postgres.health import check_postgres
        engine = get_engine()
        status = await check_postgres()
        if status.is_healthy:
            registry.register_postgres(engine)
            log.info(f"PostgreSQL ✓  latency={status.latency_ms}ms")
        else:
            log.warning(f"PostgreSQL ✗  {status.error}")
    except Exception as exc:
        log.warning(f"PostgreSQL startup failed (non-fatal): {exc}")

    # ── 2. Neo4j ───────────────────────────────────────────────────────────────
    try:
        from app.infrastructure.neo4j.driver import get_driver
        from app.infrastructure.neo4j.health import check_neo4j
        from app.modules.knowledge.infrastructure.schema_initializer import initialize_schema
        driver = await get_driver()
        status = await check_neo4j()
        if status.is_healthy:
            registry.register_neo4j(driver)
            log.info(f"Neo4j        ✓  latency={status.latency_ms}ms")
            # Initialize Knowledge Graph constraints & indexes
            await initialize_schema()
        else:
            log.warning(f"Neo4j        ✗  {status.error}")
    except Exception as exc:
        log.warning(f"Neo4j startup failed (non-fatal): {exc}")

    # ── 3. Redis ───────────────────────────────────────────────────────────────
    try:
        from app.infrastructure.redis.client import get_client
        from app.infrastructure.redis.health import check_redis
        client = get_client()
        status = await check_redis()
        if status.is_healthy:
            registry.register_redis(client)
            log.info(f"Redis        ✓  latency={status.latency_ms}ms")
        else:
            log.warning(f"Redis        ✗  {status.error}")
    except Exception as exc:
        log.warning(f"Redis startup failed (non-fatal): {exc}")

    # ── 4. Kafka EventBus ─────────────────────────────────────────────────────
    try:
        from app.infrastructure.kafka.producer import EventBus
        bus = EventBus.get()
        await bus.start()
        registry.register_event_bus(bus)
        log.info("Kafka        ✓  (EventBus ready)")
    except Exception as exc:
        log.warning(f"Kafka startup failed (non-fatal): {exc}")

    # ── 5. LLM Gateway ────────────────────────────────────────────────────────
    try:
        from app.infrastructure.llm.gateway import LLMGateway
        from app.infrastructure.llm.health import check_llm
        gateway = LLMGateway.get()
        status = await check_llm()
        registry.register_llm(gateway)
        if status.is_healthy:
            log.info(
                f"LLM          ✓  provider={gateway.provider_name} "
                f"model={gateway.model_name}"
            )
        else:
            log.warning(f"LLM          ⚠  {status.error}")
    except Exception as exc:
        log.warning(f"LLM startup failed (non-fatal): {exc}")

    # ── Ready ──────────────────────────────────────────────────────────────────
    log.info("═" * 60)
    log.info(f"ABHEDYA AI Core — Ready  {registry.status()}")
    log.info("═" * 60)

    yield  # ← application serves requests here

    # ═══════════════════════════════════════════════════════════════════════════
    # SHUTDOWN
    # ═══════════════════════════════════════════════════════════════════════════
    log.info("ABHEDYA AI Core — Shutting down…")

    # Kafka first (flush pending events)
    try:
        from app.infrastructure.kafka.producer import EventBus
        await EventBus.get().stop()
    except Exception as exc:
        log.warning(f"Kafka shutdown error: {exc}")

    # Neo4j
    try:
        from app.infrastructure.neo4j.driver import close_driver
        await close_driver()
    except Exception as exc:
        log.warning(f"Neo4j shutdown error: {exc}")

    # PostgreSQL
    try:
        from app.infrastructure.postgres.engine import close_engine
        await close_engine()
    except Exception as exc:
        log.warning(f"PostgreSQL shutdown error: {exc}")

    # Redis
    try:
        from app.infrastructure.redis.client import close_client
        await close_client()
    except Exception as exc:
        log.warning(f"Redis shutdown error: {exc}")

    log.info("ABHEDYA AI Core — Shutdown complete")
    shutdown_logging()
