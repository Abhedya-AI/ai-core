"""
filters.py — Custom logging filters.

Filters modify or suppress log records before they reach handlers.

Filters provided:
  RequestContextFilter   — injects request context into every log record
  HealthCheckFilter      — suppresses noisy health endpoint logs
  SensitiveDataFilter    — masks passwords, tokens, secrets in log messages
"""

import logging
import re
from typing import Pattern

from app.core.logging.config import LoggingConfig
from app.core.logging.request_context import get_request_context


class RequestContextFilter(logging.Filter):
    """
    Inject the current request context into every log record.

    After this filter runs, each LogRecord will have:
      record.request_id
      record.correlation_id
      record.user_id
      record.service_name
      record.environment

    These are picked up by both ConsoleFormatter and JsonFormatter.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = get_request_context()
        record.request_id = ctx.get("request_id") or "-"
        record.correlation_id = ctx.get("correlation_id") or "-"
        record.user_id = ctx.get("user_id") or "-"
        record.service_name = ctx.get("service_name") or "abhedya"
        record.environment = ctx.get("environment") or "development"
        return True  # never suppress


class HealthCheckFilter(logging.Filter):
    """
    Suppress log records originating from health-check endpoints.

    This prevents high-frequency /health polls from flooding logs,
    especially in Kubernetes liveness/readiness probe setups.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(path in message for path in LoggingConfig.SILENT_PATHS)


class SensitiveDataFilter(logging.Filter):
    """
    Mask sensitive values in log messages before they are emitted.

    Any field whose name matches a known sensitive key will have its
    value replaced with [REDACTED].

    Matched patterns (case-insensitive):
      password, passwd, token, secret, api_key, apikey,
      authorization, auth, private_key, access_token,
      refresh_token, client_secret

    Examples:
      "password=hunter2"         → "password=[REDACTED]"
      '"token": "abc123"'        → '"token": "[REDACTED]"'
      "Authorization: Bearer xy" → "Authorization: [REDACTED]"
    """

    # Pre-compiled patterns for performance
    _patterns: list[Pattern[str]] = [
        re.compile(
            rf'({re.escape(field)})'      # key
            r'(\s*[:=]\s*)'               # separator
            r'([^\s,\'"&}}\]]+)',         # value (up to whitespace/delimiter)
            re.IGNORECASE,
        )
        for field in LoggingConfig.SENSITIVE_FIELDS
    ]

    # Pattern for JSON-style quoted values
    _json_patterns: list[Pattern[str]] = [
        re.compile(
            rf'("{re.escape(field)}"'     # quoted key
            r'\s*:\s*")'                  # colon
            r'([^"]*")',                  # quoted value
            re.IGNORECASE,
        )
        for field in LoggingConfig.SENSITIVE_FIELDS
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._mask(str(record.msg))
        if record.args:
            try:
                if isinstance(record.args, dict):
                    record.args = {
                        k: self._mask(str(v)) for k, v in record.args.items()
                    }
                else:
                    record.args = tuple(
                        self._mask(str(a)) for a in record.args
                    )
            except Exception:
                pass  # never break logging due to filter error
        return True

    def _mask(self, text: str) -> str:
        for pattern in self._patterns:
            text = pattern.sub(r"\1\2[REDACTED]", text)
        for pattern in self._json_patterns:
            text = pattern.sub(r'\1[REDACTED]"', text)
        return text
