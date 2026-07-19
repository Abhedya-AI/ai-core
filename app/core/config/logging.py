"""
logging.py — Structured logging settings.

Responsibility: log level, output format, rotation policy, file path.
Nothing else. Logger construction lives in app/core/logger.py.
"""

from typing import Literal

from pydantic import Field

from app.core.config._base import _BaseConfig

LogLevel = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["text", "json"]


class LoggingSettings(_BaseConfig):
    """Loguru-based structured logging configuration."""

    level: LogLevel = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Minimum log level: TRACE | DEBUG | INFO | WARNING | ERROR | CRITICAL.",
    )
    format: LogFormat = Field(
        default="text",
        alias="LOG_FORMAT",
        description="Output format: text (human-readable) | json (structured for log aggregators).",
    )
    file: str | None = Field(
        default=None,
        alias="LOG_FILE",
        description="Path to log file. None = stdout only.",
    )
    rotation: str = Field(
        default="10 MB",
        alias="LOG_ROTATION",
        description="Log file rotation trigger: size (e.g., '10 MB') or time (e.g., '1 day').",
    )
    retention: str = Field(
        default="7 days",
        alias="LOG_RETENTION",
        description="How long to keep rotated log files.",
    )
    serialize: bool = Field(
        default=False,
        alias="LOG_SERIALIZE",
        description="Serialize log records to JSON. Automatically True when format=json.",
    )
    backtrace: bool = Field(
        default=True,
        alias="LOG_BACKTRACE",
        description="Enable extended exception tracebacks.",
    )
    diagnose: bool = Field(
        default=False,
        alias="LOG_DIAGNOSE",
        description="Enable variable values in tracebacks. Disable in production.",
    )

    @property
    def is_json(self) -> bool:
        """True when JSON log output is enabled."""
        return self.format == "json" or self.serialize
