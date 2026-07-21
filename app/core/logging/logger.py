"""
logger.py — Enterprise logger entry point.

Responsibility: configure the root logging system and expose get_logger().

Public API:
    configure_logging()   — call once at application startup (in lifespan)
    get_logger(name)      — get a named logger anywhere in the codebase
    shutdown_logging()    — flush and close all handlers at shutdown

Usage:
    from app.core.logging import get_logger

    log = get_logger(__name__)
    log.info("Server started")
    log.error("Something failed", extra={"latency_ms": 120})
"""

import logging

from app.core.logging.config import LoggingConfig
from app.core.logging.handlers import (
    create_console_handler,
    create_json_file_handler,
    create_rotating_file_handler,
)

# Track whether configure_logging() has been called
_configured: bool = False


def configure_logging() -> None:
    """
    Bootstrap the logging system.

    - Removes any existing handlers from the root logger
    - Attaches console handler (always)
    - Attaches rotating file handlers (when LOG_FILE is set)
    - Sets log levels for noisy third-party libraries

    Must be called exactly once, during FastAPI lifespan startup.
    Subsequent calls are no-ops (idempotent).
    """
    global _configured
    if _configured:
        return

    root = logging.getLogger()
    root.setLevel(LoggingConfig.LEVEL)

    # Remove any default handlers (e.g. from uvicorn)
    root.handlers.clear()

    # ── Console handler ───────────────────────────────────────────────────────
    root.addHandler(create_console_handler())

    # ── File handlers (optional) ──────────────────────────────────────────────
    if LoggingConfig.LOG_FILE:
        # Plain text file (for local archives)
        root.addHandler(create_rotating_file_handler(LoggingConfig.LOG_FILE))
        # JSON file (for log shippers like Filebeat, Promtail)
        json_path = LoggingConfig.LOG_FILE.replace(".log", ".json.log")
        root.addHandler(create_json_file_handler(json_path))

    # ── Third-party noise reduction ───────────────────────────────────────────
    # These libraries are extremely verbose at DEBUG; limit to WARNING.
    _silence = [
        "uvicorn.access",
        "httpx",
        "httpcore",
        "urllib3",
        "charset_normalizer",
        "multipart",
        "neo4j",
        "sqlalchemy.engine",
    ]
    for name in _silence:
        logging.getLogger(name).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    If configure_logging() has not been called yet, this will still work —
    Python's logging module handles it gracefully. For proper formatting,
    always call configure_logging() first in the application lifespan.

    Args:
        name: Logger name, typically __name__ or a service label.

    Returns:
        A standard library Logger instance.

    Example:
        log = get_logger(__name__)
        log = get_logger("KnowledgeGraph")
    """
    return logging.getLogger(name)


def shutdown_logging() -> None:
    """
    Flush and close all handlers cleanly.

    Call during FastAPI lifespan shutdown to ensure buffered log records
    are flushed to disk before the process exits.
    """
    global _configured
    logging.shutdown()
    _configured = False
