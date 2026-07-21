"""
_base.py — Internal helpers for the config package.

Provides:
  _ENV_FILES  - tuple of .env file paths, resolved once at startup
                based on APP_ENVIRONMENT. Imported by every settings class.

Improvement 2: dynamic env file selection
  Load order (last file wins):
    .env                 → base defaults, always loaded if present
    .env.{environment}   → e.g. .env.development, .env.production
    .env.local           → local developer overrides, never committed
"""

import os
from pathlib import Path


def _resolve_env_files() -> tuple[str, ...]:
    env = os.getenv("APP_ENVIRONMENT", "development")
    candidates = [".env", f".env.{env}", ".env.local"]
    return tuple(f for f in candidates if Path(f).exists()) or (".env",)


_ENV_FILES: tuple[str, ...] = _resolve_env_files()
