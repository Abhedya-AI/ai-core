"""
Structured logger for ABHEDYA.

Usage:
    from app.core.logger import get_logger

    log = get_logger("GraphService")
    log.info("Connected to Neo4j")

Output:
    2026-07-02 10:42:12
    INFO
    GraphService
    Connected to Neo4j
"""

import sys
from loguru import logger as _base_logger

from app.core.config.settings import logging_config


def _formatter(record: dict) -> str:
    service = record["extra"].get("service", "ABHEDYA")
    return (
        "{time:YYYY-MM-DD HH:mm:ss}\n"
        "{level}\n"
        f"{service}\n"
        "{message}\n\n"
    )


# ── Bootstrap ─────────────────────────────────────────────────────────────────
_base_logger.remove()
_base_logger.add(sys.stdout, format=_formatter, level=logging_config.log_level, colorize=False)

if logging_config.log_file:
    _base_logger.add(
        logging_config.log_file,
        format=_formatter,
        level=logging_config.log_level,
        rotation="10 MB",
        retention="7 days",
    )


# ── Public API ────────────────────────────────────────────────────────────────
def get_logger(service: str):
    """Return a logger bound to a specific service name."""
    return _base_logger.bind(service=service)


# Default application-level logger
logger = get_logger("ABHEDYA")
