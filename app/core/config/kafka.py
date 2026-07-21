from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config._base import _ENV_FILES


class KafkaSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_prefix="KAFKA_",        # Improvement 1: env_prefix
        env_file=_ENV_FILES,        # Improvement 2: dynamic env file
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bootstrap_servers: str = Field(default="localhost:9092")
    client_id: str = Field(default="abhedya")
    consumer_group: str = Field(default="abhedya-group")
    enabled: bool = Field(default=False)

    @property
    def broker_list(self) -> list[str]:
        return [s.strip() for s in self.bootstrap_servers.split(",")]
