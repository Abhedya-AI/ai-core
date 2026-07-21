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
    _loguru.remove()

    if _cfg.json_logs:
        _loguru.add(sys.stdout, level=_cfg.level, serialize=True)
    else:
        _loguru.add(
            sys.stdout,
            format=_build_format("ABHEDYA"),
            level=_cfg.level,
            colorize=False,
        )

    if _cfg.file:
        _loguru.add(
            _cfg.file,
            format=_build_format("ABHEDYA"),
            level=_cfg.level,
            rotation=_cfg.rotation,
            retention=_cfg.retention,
        )


_configure_logger()


def get_logger(service: str):
    """Return a loguru logger bound to a service name."""
    return _loguru.bind(service=service)


logger = get_logger("ABHEDYA")
