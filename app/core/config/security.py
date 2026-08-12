import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config._base import _ENV_FILES

_DEFAULT_SECRET = "abhedya-dev-secret-change-this-before-production-deployment-64chars"


class SecuritySettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,        # Improvement 2: dynamic env file
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # These keep their conventional names (no prefix) — industry standard
    secret_key: str = Field(default=_DEFAULT_SECRET, alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="ALLOWED_ORIGINS",
    )

    @field_validator("secret_key")
    @classmethod
    def _reject_default_in_production(cls, v: str) -> str:
        if os.getenv("APP_ENVIRONMENT") == "production" and v == _DEFAULT_SECRET:
            raise ValueError(
                "SECRET_KEY must be changed before deploying to production."
            )
        return v

    @property
    def is_key_unsafe(self) -> bool:
        return self.secret_key == _DEFAULT_SECRET
