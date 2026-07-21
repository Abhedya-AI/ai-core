"""
ABHEDYA Enterprise Logging Package.

Public API — import only these two names:

    from app.core.logging import get_logger, configure_logging

    configure_logging()          # call once in lifespan startup
    log = get_logger(__name__)   # call anywhere
    log.info("Ready")
"""

from app.core.logging.logger import configure_logging, get_logger

__all__ = ["get_logger", "configure_logging"]
