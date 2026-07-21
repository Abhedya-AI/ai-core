"""
kafka/producer.py — EventBus: the only way to publish Kafka events.

No code outside this module should call AIOKafkaProducer directly.
All events flow through EventBus.publish().

Usage:
    from app.infrastructure.kafka.producer import EventBus

    bus = EventBus.get()
    await bus.publish(
        topic=Topics.SENSOR_READING_CREATED,
        payload={"sensor_id": "S-001", "value": 42.3},
        key="S-001",
    )
"""

import json
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("kafka.producer")


class EventBus:
    """
    Async event publisher.

    When KAFKA_ENABLED=False (the default), publish() is a no-op that logs
    the event locally. This allows development without a running Kafka broker.

    When KAFKA_ENABLED=True, events are published to the real broker.
    """

    _instance: "EventBus | None" = None
    _producer = None

    @classmethod
    def get(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(self) -> None:
        """Initialize the producer. Called during application startup."""
        if not settings.kafka.enabled:
            log.info("Kafka disabled — EventBus running in no-op mode")
            return
        try:
            from aiokafka import AIOKafkaProducer
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka.bootstrap_servers,
                client_id=settings.kafka.client_id,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                compression_type="gzip",
                acks="all",                # wait for all replicas
                retries=3,
            )
            await self._producer.start()
            log.info(f"Kafka producer started → {settings.kafka.bootstrap_servers}")
        except Exception as exc:
            log.error(f"Failed to start Kafka producer: {exc}")
            self._producer = None

    async def stop(self) -> None:
        """Flush and close the producer. Called during application shutdown."""
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
            log.info("Kafka producer stopped")

    async def publish(
        self,
        topic: str,
        payload: dict[str, Any],
        key: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> bool:
        """
        Publish an event to a Kafka topic.

        Args:
            topic:   Topic name — always use Topics.* constants, never raw strings.
            payload: Event payload (must be JSON-serialisable).
            key:     Optional partition key (e.g. sensor_id for ordering).
            headers: Optional Kafka headers for metadata.

        Returns:
            True on success, False on failure (logs the error, never raises).
        """
        if not settings.kafka.enabled or self._producer is None:
            log.debug(f"[no-op] Kafka event: {topic} → {payload}")
            return True
        try:
            kafka_headers = None
            if headers:
                kafka_headers = [
                    (k, v.encode("utf-8")) for k, v in headers.items()
                ]
            await self._producer.send_and_wait(
                topic,
                value=payload,
                key=key,
                headers=kafka_headers,
            )
            log.debug(f"Event published: {topic} key={key}")
            return True
        except Exception as exc:
            log.error(f"Failed to publish event to {topic!r}: {exc}")
            return False
