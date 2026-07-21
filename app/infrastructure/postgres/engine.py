"""
postgres/engine.py — Async SQLAlchemy engine singleton.

Responsibility: create and manage the engine lifecycle.
No session creation here — that lives in session.py.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.logging import get_logger
from app.infrastructure.postgres.config import PostgresConfig

log = get_logger("postgres.engine")

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """
    Return the async engine singleton, creating it on first call.

    The engine is created once and reused for the lifetime of the process.
    Connection pooling is managed by SQLAlchemy automatically.
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            PostgresConfig.ASYNC_URL,
            echo=PostgresConfig.ECHO_SQL,
            pool_pre_ping=PostgresConfig.POOL_PRE_PING,
            pool_size=PostgresConfig.POOL_SIZE,
            max_overflow=PostgresConfig.MAX_OVERFLOW,
            pool_timeout=PostgresConfig.POOL_TIMEOUT,
            pool_recycle=PostgresConfig.POOL_RECYCLE,
            connect_args={
                "timeout": PostgresConfig.CONNECT_TIMEOUT,
                "command_timeout": PostgresConfig.COMMAND_TIMEOUT,
            },
        )
        log.info(
            f"Async engine created → "
            f"{PostgresConfig.HOST}:{PostgresConfig.PORT}/{PostgresConfig.DATABASE}"
        )
    return _engine


async def close_engine() -> None:
    """Dispose the engine and release all pooled connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        log.info("PostgreSQL engine disposed")
