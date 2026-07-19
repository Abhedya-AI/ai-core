"""
kafka.py — Apache Kafka event streaming settings.

Responsibility: broker addresses, topic names, consumer group, producer config.
Disabled by default. Enabled in Milestone 6+ (Emergency Response).

Usage:
    from app.core.config import settings
    if settings.kafka.enabled:
        producer = KafkaProducer(settings.kafka.bootstrap_servers)
"""

from pydantic import Field

from app.core.config._base import _BaseConfig


class KafkaSettings(_BaseConfig):
    """Apache Kafka event streaming configuration."""

    enabled: bool = Field(
        default=False,
        alias="KAFKA_ENABLED",
        description="Enable Kafka event streaming. False until Milestone 6.",
    )
    bootstrap_servers: str = Field(
        default="localhost:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS",
        description="Comma-separated list of Kafka broker addresses.",
    )

    # ── Consumer ─────────────────────────────────────────────────────────────
    consumer_group: str = Field(
        default="abhedya-core",
        alias="KAFKA_CONSUMER_GROUP",
        description="Kafka consumer group ID.",
    )
    auto_offset_reset: str = Field(
        default="earliest",
        alias="KAFKA_AUTO_OFFSET_RESET",
        description="Where to start consuming: earliest | latest.",
    )
    session_timeout_ms: int = Field(
        default=30_000,
        alias="KAFKA_SESSION_TIMEOUT_MS",
        description="Consumer session timeout in milliseconds.",
    )

    # ── Producer ─────────────────────────────────────────────────────────────
    acks: str = Field(
        default="all",
        alias="KAFKA_ACKS",
        description="Producer acknowledgement level: 0 | 1 | all.",
    )
    retries: int = Field(
        default=3,
        alias="KAFKA_RETRIES",
        description="Number of producer retries on failure.",
    )
    batch_size: int = Field(
        default=16_384,
        alias="KAFKA_BATCH_SIZE",
        description="Producer batch size in bytes.",
    )
    linger_ms: int = Field(
        default=5,
        alias="KAFKA_LINGER_MS",
        description="Producer linger time before sending a batch.",
    )

    # ── Topics ───────────────────────────────────────────────────────────────
    topic_alerts: str = Field(
        default="abhedya.alerts",
        alias="KAFKA_TOPIC_ALERTS",
        description="Topic for real-time alert events.",
    )
    topic_incidents: str = Field(
        default="abhedya.incidents",
        alias="KAFKA_TOPIC_INCIDENTS",
        description="Topic for incident lifecycle events.",
    )
    topic_audit: str = Field(
        default="abhedya.audit",
        alias="KAFKA_TOPIC_AUDIT",
        description="Topic for audit log events.",
    )
    topic_geo: str = Field(
        default="abhedya.geo",
        alias="KAFKA_TOPIC_GEO",
        description="Topic for geospatial intelligence events.",
    )

    @property
    def broker_list(self) -> list[str]:
        """Return broker addresses as a list."""
        return [b.strip() for b in self.bootstrap_servers.split(",")]
