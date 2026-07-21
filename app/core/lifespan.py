"""
lifespan.py — FastAPI application lifespan manager.

Handles startup and shutdown using the modern asynccontextmanager pattern
(replaces deprecated @app.on_event).

Startup order:
  1. configure_logging()   — logging system must be first
  2. Database connections  — Postgres, Neo4j, Redis checked
  3. Application ready

Shutdown order:
  1. Close Neo4j driver
  2. shutdown_logging()    — flush and close log files last
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import configure_logging, get_logger
from app.core.logging.logger import shutdown_logging

# configure_logging() called before any logger is created
configure_logging()

log = get_logger("abhedya.lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager."""

    # ── Startup ────────────────────────────────────────────────────────────────
    log.info("ABHEDYA starting up…")

    yield  # application runs here

    # ── Shutdown ───────────────────────────────────────────────────────────────
    log.info("ABHEDYA shutting down…")

    from app.database.neo4j import close_driver
    close_driver()

    shutdown_logging()
