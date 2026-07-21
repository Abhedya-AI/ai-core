"""
formatter.py — Log record formatters.

Formatters provided:
  ConsoleFormatter  — human-readable, ANSI-colored output for development
  JsonFormatter     — structured JSON output for ELK / Grafana Loki / Datadog

Both formatters expect the RequestContextFilter to have already enriched
each LogRecord with request_id, correlation_id, user_id, service_name,
and environment attributes.
"""

import json
import logging
import traceback
from datetime import datetime, timezone

from app.core.logging.config import LoggingConfig

# ── ANSI color codes ──────────────────────────────────────────────────────────
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_LEVEL_COLORS: dict[str, str] = {
    "DEBUG":    "\033[36m",    # Cyan
    "INFO":     "\033[32m",    # Green
    "WARNING":  "\033[33m",    # Yellow
    "ERROR":    "\033[31m",    # Red
    "CRITICAL": "\033[35m",    # Magenta
}


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable, ANSI-colored formatter for development.

    Output format:
        [2026-07-21 23:15:01]
        INFO
        service_name
        Your log message here
        request_id=93ac...  correlation_id=991e...
    """

    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelname, _RESET)
        timestamp = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime(LoggingConfig.DATE_FORMAT)

        # Core fields
        service = getattr(record, "service_name", record.name)
        request_id = getattr(record, "request_id", "-")
        correlation_id = getattr(record, "correlation_id", "-")

        # Format the message and optional exception
        message = record.getMessage()
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)

        # Build context suffix (only if request_id is set)
        context = ""
        if request_id and request_id != "-":
            context = (
                f"\n{_DIM}request_id={request_id}"
                f"  correlation_id={correlation_id}{_RESET}"
            )

        return (
            f"{_DIM}[{timestamp}]{_RESET}\n"
            f"{color}{_BOLD}{record.levelname}{_RESET}\n"
            f"{_BOLD}{service}{_RESET}\n"
            f"{message}"
            f"{context}\n"
        )


class JsonFormatter(logging.Formatter):
    """
    Structured JSON formatter for production log aggregators.

    Each log record is emitted as a single-line JSON object, ready for
    ingestion by ELK Stack, Grafana Loki, Datadog, or Google Cloud Logging.

    Output fields:
        timestamp       ISO 8601 UTC
        level           INFO / ERROR / etc.
        logger          Python logger name
        service         service_name from request context
        message         log message
        request_id      per-request UUID
        correlation_id  distributed tracing ID
        user_id         authenticated user (null if unauthenticated)
        environment     development | production
        file            source file name
        line            source line number
        exc_info        exception traceback (only when present)
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "service": getattr(record, "service_name", record.name),
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "correlation_id": getattr(record, "correlation_id", None),
            "user_id": getattr(record, "user_id", None),
            "environment": getattr(record, "environment", None),
            "file": record.filename,
            "line": record.lineno,
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Include any extra fields attached to the record
        standard_keys = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "request_id", "correlation_id", "user_id", "service_name",
            "environment", "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in standard_keys and not key.startswith("_"):
                try:
                    json.dumps(value)  # only include JSON-serialisable extras
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = str(value)

        return json.dumps(payload, ensure_ascii=False)
