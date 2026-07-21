"""
logger.py — Backward-compatibility shim.

The canonical logging module is now app.core.logging.
This file re-exports get_logger so existing imports continue to work
without changes during the migration period.

    # Old imports still work:
    from app.core.logger import get_logger

    # New canonical import:
    from app.core.logging import get_logger
"""

from app.core.logging import configure_logging, get_logger  # noqa: F401

__all__ = ["get_logger", "configure_logging"]
