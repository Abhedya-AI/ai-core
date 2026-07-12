from pydantic import Field
from pydantic_settings import BaseSettings

from app.core.config.database import DatabaseSettings
from app.core.config.llm import LLMSettings
from app.core.config.logging import LoggingSettings
from app.core.config.security import SecuritySettings


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = Field("ABHEDYA", alias="APP_NAME")
    app_env: str = Field("development", alias="APP_ENV")
    app_debug: bool = Field(True, alias="APP_DEBUG")
    api_version: str = Field("v1", alias="API_VERSION")
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")

    model_config = {"env_file": ".env", "extra": "ignore", "populate_by_name": True}

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# ── Singleton instances (import these, not Settings directly) ────────────────
settings = Settings()
database = DatabaseSettings()
llm = LLMSettings()
security = SecuritySettings()
logging_config = LoggingSettings()
