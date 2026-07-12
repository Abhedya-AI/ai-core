from pydantic import Field
from pydantic_settings import BaseSettings


class KafkaSettings(BaseSettings):
    """
    Kafka / event streaming settings.

    Placeholder for Milestone 6+ (Emergency Response, Real-time Intelligence).
    Enable by setting KAFKA_ENABLED=True in .env.
    """

    kafka_enabled: bool = Field(False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(
        "localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_consumer_group: str = Field("abhedya-core", alias="KAFKA_CONSUMER_GROUP")

    model_config = {"env_file": ".env", "extra": "ignore", "populate_by_name": True}
