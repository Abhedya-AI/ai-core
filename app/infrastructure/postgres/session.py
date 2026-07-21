"""
postgres/session.py — Async session factory and FastAPI dependency.

Responsibility: create async sessions. No engine creation here.

Usage (FastAPI route):
    from app.infrastructure.postgres.session import get_session
    from sqlalchemy.ext.asyncio import AsyncSession

    @router.get("/items")
    async def list_items(session: AsyncSession = Depends(get_session)):
        result = await session.execute(select(Item))
        return result.scalars().all()
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logging import get_logger
from app.infrastructure.postgres.engine import get_engine

log = get_logger("postgres.session")

_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory singleton."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session.

    Automatically rolls back on exception and always closes the session.

    Usage:
        async def route(session: AsyncSession = Depends(get_session)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
