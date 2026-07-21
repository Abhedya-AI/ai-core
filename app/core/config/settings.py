from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config._base import _ENV_FILES
from app.core.config.app import AppSettings
from app.core.config.database import Neo4jSettings, PostgresSettings, RedisSettings
from app.core.config.kafka import KafkaSettings
from app.core.config.llm import LLMSettings
from app.core.config.logging import LoggingSettings
from app.core.config.security import SecuritySettings


class Settings(BaseSettings):
    """
    Root settings object.

    Composes all domain-specific settings into a single access point.

    Usage:
        from app.core.config import settings

        settings.app.name
        settings.app.is_production
        settings.database.url
        settings.neo4j.uri
        settings.redis.url
        settings.llm.provider
        settings.llm.active_api_key
        settings.kafka.enabled
        settings.logging.level
        settings.security.secret_key
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,        # Improvement 2: dynamic env file selection
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app: AppSettings = AppSettings()
    database: PostgresSettings = PostgresSettings()
    neo4j: Neo4jSettings = Neo4jSettings()
    redis: RedisSettings = RedisSettings()
    llm: LLMSettings = LLMSettings()
    kafka: KafkaSettings = KafkaSettings()
    logging: LoggingSettings = LoggingSettings()
    security: SecuritySettings = SecuritySettings()


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton. Called once per process lifetime."""
    return Settings()
