"""
handlers.py — Logging handler factories.

Responsibility: create and configure logging handlers.
No logger creation. No formatter selection logic (that lives in logger.py).

Handlers provided:
  create_console_handler()      — stdout, colored (dev) or JSON (prod)
  create_rotating_file_handler() — plain text rotating file
  create_json_file_handler()    — JSON rotating file for log aggregators
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core.logging.config import LoggingConfig
from app.core.logging.filters import (
    HealthCheckFilter,
    RequestContextFilter,
    SensitiveDataFilter,
)
from app.core.logging.formatter import ConsoleFormatter, JsonFormatter


def _attach_common_filters(handler: logging.Handler) -> None:
    """Attach filters that apply to every handler."""
    handler.addFilter(RequestContextFilter())
    handler.addFilter(SensitiveDataFilter())


def create_console_handler() -> logging.StreamHandler:
    """
    Return a stdout handler.

    Uses ConsoleFormatter in development (human-readable, colored).
    Uses JsonFormatter in production (JSON_LOGS=True).
    Includes a HealthCheckFilter to suppress /health endpoint noise.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(LoggingConfig.LEVEL)

    if LoggingConfig.JSON_LOGS:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    handler.addFilter(HealthCheckFilter())
    _attach_common_filters(handler)
    return handler


def create_rotating_file_handler(filepath: str) -> RotatingFileHandler:
    """
    Return a plain-text rotating file handler.

    Rotation: every 10 MB, keeping 5 backups.
    Does NOT suppress health check logs (file logs should be complete).
    """
    handler = RotatingFileHandler(
        filepath,
        maxBytes=LoggingConfig.MAX_BYTES,
        backupCount=LoggingConfig.BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(LoggingConfig.LEVEL)
    handler.setFormatter(
        logging.Formatter(
            fmt=LoggingConfig.LOG_FORMAT,
            datefmt=LoggingConfig.DATE_FORMAT,
            style="{",
        )
    )
    _attach_common_filters(handler)
    return handler


def create_json_file_handler(filepath: str) -> RotatingFileHandler:
    """
    Return a JSON rotating file handler for log aggregators.

    Writes one JSON object per line. Suitable for Filebeat → Elasticsearch,
    Promtail → Grafana Loki, or Fluentd → Datadog.

    Rotation: every 10 MB, keeping 5 backups.
    """
    handler = RotatingFileHandler(
        filepath,
        maxBytes=LoggingConfig.MAX_BYTES,
        backupCount=LoggingConfig.BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(LoggingConfig.LEVEL)
    handler.setFormatter(JsonFormatter())
    _attach_common_filters(handler)
    return handler
