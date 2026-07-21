from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config._base import _ENV_FILES


class LoggingSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_prefix="LOG_",          # Improvement 1: env_prefix
        env_file=_ENV_FILES,        # Improvement 2: dynamic env file
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    json_logs: bool = Field(default=False)
    file: str | None = Field(default=None)
    rotation: str = Field(default="10 MB")
    retention: str = Field(default="7 days")
