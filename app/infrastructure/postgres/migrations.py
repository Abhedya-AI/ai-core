"""
postgres/migrations.py — Alembic migration helpers.

Responsibility: programmatic Alembic integration.
Actual migration files live in alembic/versions/.

Usage (from lifespan):
    from app.infrastructure.postgres.migrations import run_migrations
    await run_migrations()
"""

import asyncio

from app.core.logging import get_logger

log = get_logger("postgres.migrations")


async def run_migrations() -> None:
    """
    Run pending Alembic migrations at startup.

    Runs in a thread pool executor because Alembic uses a synchronous API.
    Safe to call multiple times — Alembic tracks applied migrations.

    Note: In production, prefer running migrations as a pre-startup job
    rather than automatically on every boot.
    """
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _run_alembic_upgrade)
        log.info("Database migrations applied successfully")
    except Exception as exc:
        log.warning(f"Migration step skipped (alembic may not be configured yet): {exc}")


def _run_alembic_upgrade() -> None:
    """Synchronous Alembic upgrade call — must run in executor."""
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        raise RuntimeError(f"Alembic upgrade failed: {exc}") from exc
