from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config._base import _ENV_FILES


class AppSettings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",          # Improvement 1: env_prefix
        env_file=_ENV_FILES,        # Improvement 2: dynamic env file
        env_file_encoding="utf-8",
        extra="ignore",
    )

    name: str = Field(default="ABHEDYA AI Core")
    version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    api_prefix: str = Field(default="/api/v1")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"
