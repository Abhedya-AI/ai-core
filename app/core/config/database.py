from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config._base import _ENV_FILES


class PostgresSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",     # Improvement 1: env_prefix
        env_file=_ENV_FILES,        # Improvement 2: dynamic env file
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="abhedya")
    username: str = Field(default="postgres")
    password: str = Field(default="postgres")

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class Neo4jSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_prefix="NEO4J_",        # Improvement 1: env_prefix
        env_file=_ENV_FILES,        # Improvement 2: dynamic env file
        env_file_encoding="utf-8",
        extra="ignore",
    )

    uri: str = Field(default="bolt://localhost:7687")
    username: str = Field(default="neo4j")
    password: str = Field(default="password")


class RedisSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",        # Improvement 1: env_prefix
        env_file=_ENV_FILES,        # Improvement 2: dynamic env file
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    password: str | None = Field(default=None)
    db: int = Field(default=0)

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
