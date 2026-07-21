"""
app/core/registry.py — Service Registry.

The registry is the single source of truth for all live infrastructure clients.
Every module that needs a database connection, cache, or LLM client
requests it from the registry instead of creating its own.

Usage:
    from app.core.registry import registry

    # In a route:
    session = await registry.postgres_session()

    # In GraphRAG:
    driver = registry.neo4j_driver
    cache  = registry.redis_cache("graphrag")
    llm    = registry.llm
"""

from __future__ import annotations

from app.core.logging import get_logger

log = get_logger("registry")


class ServiceRegistry:
    """
    Central registry for all infrastructure singletons.

    Populated by the lifespan manager during startup.
    All fields are None until the corresponding service is initialized.
    """

    def __init__(self) -> None:
        # ── Clients ────────────────────────────────────────────────────────────
        from sqlalchemy.ext.asyncio import AsyncEngine
        from neo4j import AsyncDriver
        from redis.asyncio import Redis
        from app.infrastructure.llm.gateway import LLMGateway
        from app.infrastructure.kafka.producer import EventBus

        self._postgres_engine: AsyncEngine | None = None
        self._neo4j_driver: AsyncDriver | None = None
        self._redis_client: Redis | None = None
        self._llm: LLMGateway | None = None
        self._event_bus: EventBus | None = None

    # ── PostgreSQL ─────────────────────────────────────────────────────────────

    def register_postgres(self, engine) -> None:
        self._postgres_engine = engine
        log.info("✓ PostgreSQL registered")

    @property
    def postgres(self):
        if self._postgres_engine is None:
            raise RuntimeError("PostgreSQL engine not registered in ServiceRegistry")
        return self._postgres_engine

    # ── Neo4j ──────────────────────────────────────────────────────────────────

    def register_neo4j(self, driver) -> None:
        self._neo4j_driver = driver
        log.info("✓ Neo4j registered")

    @property
    def neo4j(self):
        if self._neo4j_driver is None:
            raise RuntimeError("Neo4j driver not registered in ServiceRegistry")
        return self._neo4j_driver

    # ── Redis ──────────────────────────────────────────────────────────────────

    def register_redis(self, client) -> None:
        self._redis_client = client
        log.info("✓ Redis registered")

    @property
    def redis(self):
        if self._redis_client is None:
            raise RuntimeError("Redis client not registered in ServiceRegistry")
        return self._redis_client

    def redis_cache(self, prefix: str, ttl: int = 300):
        """
        Return a namespaced CacheService for a given module.

        Args:
            prefix: Namespace (e.g. "graphrag", "llm", "session").
            ttl:    Default TTL in seconds.
        """
        from app.infrastructure.redis.cache import CacheService
        return CacheService(prefix=prefix, default_ttl=ttl)

    # ── LLM ───────────────────────────────────────────────────────────────────

    def register_llm(self, gateway) -> None:
        self._llm = gateway
        log.info(f"✓ LLM registered (provider={gateway.provider_name})")

    @property
    def llm(self):
        if self._llm is None:
            raise RuntimeError("LLM gateway not registered in ServiceRegistry")
        return self._llm

    # ── Kafka EventBus ────────────────────────────────────────────────────────

    def register_event_bus(self, bus) -> None:
        self._event_bus = bus
        log.info("✓ Kafka EventBus registered")

    @property
    def event_bus(self):
        if self._event_bus is None:
            raise RuntimeError("EventBus not registered in ServiceRegistry")
        return self._event_bus

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> dict[str, bool]:
        """Return registration status of all services."""
        return {
            "postgres": self._postgres_engine is not None,
            "neo4j": self._neo4j_driver is not None,
            "redis": self._redis_client is not None,
            "llm": self._llm is not None,
            "event_bus": self._event_bus is not None,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
registry = ServiceRegistry()
