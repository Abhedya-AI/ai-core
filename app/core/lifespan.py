"""
Application lifespan manager.

Handles startup and shutdown events using the modern FastAPI lifespan pattern
(replaces deprecated @app.on_event).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logger import get_logger

log = get_logger("Lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Startup:  initialise resources
    Shutdown: cleanly release resources
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    log.info("ABHEDYA starting up…")

    yield  # application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    log.info("ABHEDYA shutting down…")

    from app.database.neo4j import close_driver
    close_driver()
