"""
_base.py — Shared base configuration class.

Resolves env files in priority order (later files override earlier ones):
  1. .env                  → base defaults, always loaded
  2. .env.{APP_ENV}        → environment-specific overrides
  3. .env.local            → local developer overrides, never committed

Every sub-settings class inherits from _BaseConfig so they all load from
the same resolved set of env files without repeating the logic.

This module is internal — do NOT import it directly from outside the config package.
"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_files() -> tuple[str, ...]:
    """
    Determine which .env files exist and should be loaded, in priority order.

    Returns a tuple of file path strings for existing files only.
    Pydantic-settings loads them left-to-right; rightmost values win.
    """
    app_env = os.getenv("APP_ENV", "development")

    candidates: list[str] = [
        ".env",
        f".env.{app_env}",   # e.g. .env.development, .env.production
        ".env.local",        # always highest priority, never committed
    ]

    return tuple(path for path in candidates if Path(path).exists())


# Resolved once at import time
_ENV_FILES: tuple[str, ...] = _resolve_env_files()


class _BaseConfig(BaseSettings):
    """
    Shared base for all ABHEDYA settings classes.

    Loads from the resolved env file stack and enables field population
    by both the Pydantic field name and the env-var alias.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES if _ENV_FILES else (".env",),
        env_file_encoding="utf-8",
        extra="ignore",           # silently ignore unknown env vars
        populate_by_name=True,    # allow both field name and alias
    )
