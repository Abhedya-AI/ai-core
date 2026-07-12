"""
ABHEDYA Configuration Package.

Import pattern used throughout the project:

    from app.core.config import settings          # App-level settings
    from app.core.config import database          # DB connection settings
    from app.core.config import llm               # LLM provider settings
    from app.core.config import security          # Auth/CORS settings
    from app.core.config import logging_config    # Logging settings
    from app.core.config import kafka             # Event streaming settings

No module should ever call os.getenv() or load .env directly.
"""

from app.core.config.settings import (
    settings,
    database,
    llm,
    security,
    logging_config,
)
from app.core.config.kafka import KafkaSettings

kafka = KafkaSettings()

__all__ = [
    "settings",
    "database",
    "llm",
    "security",
    "logging_config",
    "kafka",
]
