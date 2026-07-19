"""
settings.py — Root settings composer and singleton.

Responsibility:
  1. Instantiate each sub-settings class
  2. Compose them into a single object
  3. Validate cross-cutting concerns at startup
  4. Expose a cached singleton

Usage (anywhere in the project):
    from app.core.config import settings

    settings.app.name           → "ABHEDYA"
    settings.app.is_production  → False
    settings.database.url       → "postgresql://..."
    settings.neo4j.uri          → "bolt://localhost:7687"
    settings.redis.url          → "redis://localhost:6379/0"
    settings.llm.provider       → "gemini"
    settings.llm.active_api_key → "<your-key>"
    settings.security.secret_key
    settings.kafka.enabled
    settings.logging.level
    settings.vector_store.index_path
"""

from functools import lru_cache

from app.core.config.app import AppSettings
from app.core.config.database import (
    DatabaseSettings,
    Neo4jSettings,
    RedisSettings,
    VectorStoreSettings,
)
from app.core.config.kafka import KafkaSettings
from app.core.config.llm import LLMSettings
from app.core.config.logging import LoggingSettings
from app.core.config.security import SecuritySettings


class Settings:
    """
    Root settings object.

    Composes all sub-settings into a single access point.
    Each attribute is a lazily validated Pydantic model.

    This class must remain thin — no business logic.
    """

    def __init__(self) -> None:
        # ── Sub-settings instantiation ────────────────────────────────────────
        self.app: AppSettings = AppSettings()
        self.database: DatabaseSettings = DatabaseSettings()
        self.neo4j: Neo4jSettings = Neo4jSettings()
        self.redis: RedisSettings = RedisSettings()
        self.vector_store: VectorStoreSettings = VectorStoreSettings()
        self.llm: LLMSettings = LLMSettings()
        self.kafka: KafkaSettings = KafkaSettings()
        self.logging: LoggingSettings = LoggingSettings()
        self.security: SecuritySettings = SecuritySettings()

        # ── Cross-cutting startup validation ──────────────────────────────────
        self._validate()

    def _validate(self) -> None:
        """
        Fail fast on critical misconfigurations.

        These checks run once at startup.
        They prevent silent misconfiguration in production.
        """
        if self.app.is_production:
            errors: list[str] = []

            if self.security.is_key_unsafe:
                errors.append(
                    "SECRET_KEY is set to the default placeholder. "
                    "Generate a strong secret and set it in .env.production."
                )

            if self.app.debug:
                errors.append(
                    "APP_DEBUG=True in production. Set APP_DEBUG=False."
                )

            if self.llm.active_api_key is None:
                errors.append(
                    f"LLM_PROVIDER='{self.llm.provider}' but "
                    f"no API key is configured. "
                    f"Set {self.llm.provider.upper()}_API_KEY."
                )

            if errors:
                raise EnvironmentError(
                    "ABHEDYA refused to start due to production misconfiguration:\n"
                    + "\n".join(f"  ✗ {e}" for e in errors)
                )

    def __repr__(self) -> str:
        return (
            f"Settings("
            f"app={self.app.name!r}, "
            f"env={self.app.env!r}, "
            f"debug={self.app.debug}, "
            f"llm_provider={self.llm.provider!r}"
            f")"
        )


@lru_cache(maxsize=1)
def _create_settings() -> Settings:
    """
    Create and cache the Settings singleton.

    lru_cache ensures only one instance exists for the lifetime of the process.
    """
    return Settings()


# ── Module-level singleton ─────────────────────────────────────────────────────
# Import this, not Settings() directly.
settings: Settings = _create_settings()
