"""
logger.py — Structured logging for ABHEDYA.

Usage:
    from app.core.logger import get_logger

    log = get_logger("GraphService")
    log.info("Connected to Neo4j")

Output format:
    2026-07-19 11:25:00
    INFO
    GraphService
    Connected to Neo4j

Each service gets its own named logger via get_logger().
The root logger is also exported for convenience.
"""

import sys
from loguru import logger as _loguru

from app.core.config import settings

_cfg = settings.logging


def _build_format(service: str) -> str:
    """Return a loguru format string with the service name embedded."""
    return (
        "{time:YYYY-MM-DD HH:mm:ss}\n"
        "{level}\n"
        f"{service}\n"
        "{message}\n"
    )


def _configure_logger() -> None:
    """Bootstrap the loguru logger from LoggingSettings."""
    _loguru.remove()  # Remove default handler

    # ── Stdout handler ────────────────────────────────────────────────────────
    if _cfg.is_json:
        # Structured JSON output for log aggregators (e.g. Loki, Datadog)
        _loguru.add(
            sys.stdout,
            level=_cfg.level,
            serialize=True,
            backtrace=_cfg.backtrace,
            diagnose=_cfg.diagnose,
        )
    else:
        # Human-readable multiline format for local development
        _loguru.add(
            sys.stdout,
            format=_build_format("ABHEDYA"),
            level=_cfg.level,
            colorize=False,
            backtrace=_cfg.backtrace,
            diagnose=_cfg.diagnose,
        )

    # ── File handler (optional) ───────────────────────────────────────────────
    if _cfg.file:
        _loguru.add(
            _cfg.file,
            format=_build_format("ABHEDYA"),
            level=_cfg.level,
            rotation=_cfg.rotation,
            retention=_cfg.retention,
            backtrace=_cfg.backtrace,
            diagnose=_cfg.diagnose,
        )


# Bootstrap once at import time
_configure_logger()


# ── Public API ─────────────────────────────────────────────────────────────────

def get_logger(service: str):
    """
    Return a loguru logger bound to a service name.

    The service name appears on the third line of every log entry.

    Example:
        log = get_logger("KnowledgeGraph")
        log.info("Loaded 1,024 nodes")
    """
    return _loguru.bind(service=service)


# Root logger for use in this module or as a default
logger = get_logger("ABHEDYA")
