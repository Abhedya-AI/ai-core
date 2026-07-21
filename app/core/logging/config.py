"""
config.py — Logging configuration values.

Responsibility: expose logging configuration as typed constants.
No logger creation. No handler creation. No formatting.

Every other logging module reads from this file.
"""

from app.core.config import settings

_s = settings.logging


class LoggingConfig:
    """Centralised logging configuration constants."""

    # ── Core ──────────────────────────────────────────────────────────────────
    LEVEL: str = _s.level
    JSON_LOGS: bool = _s.json_logs
    LOG_FILE: str | None = _s.file

    # ── File rotation ─────────────────────────────────────────────────────────
    MAX_BYTES: int = 10 * 1024 * 1024   # 10 MB
    BACKUP_COUNT: int = 5

    # ── Formatting ────────────────────────────────────────────────────────────
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    LOG_FORMAT: str = "[{asctime}]\n{levelname}\n{name}\n{message}"

    # ── Sensitive field names that must never appear in logs ─────────────────
    SENSITIVE_FIELDS: frozenset[str] = frozenset({
        "password",
        "passwd",
        "token",
        "secret",
        "api_key",
        "apikey",
        "authorization",
        "auth",
        "private_key",
        "access_token",
        "refresh_token",
        "client_secret",
    })

    # ── Paths excluded from request logging ───────────────────────────────────
    SILENT_PATHS: frozenset[str] = frozenset({
        "/health",
        "/api/v1/health",
        "/metrics",
        "/favicon.ico",
        "/robots.txt",
    })
