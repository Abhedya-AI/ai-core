from pydantic import Field
from pydantic_settings import BaseSettings


class LoggingSettings(BaseSettings):
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_format: str = Field("text", alias="LOG_FORMAT")   # "text" | "json"
    log_file: str | None = Field(None, alias="LOG_FILE")

    model_config = {"env_file": ".env", "extra": "ignore", "populate_by_name": True}
