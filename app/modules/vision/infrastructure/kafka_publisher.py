"""
infrastructure/kafka_publisher.py — Kafka event publisher (infrastructure adapter).

This is the infrastructure-layer adapter that wraps the ABHEDYA
EventBus.  The application layer (publish_event.py) calls this adapter
rather than the EventBus directly, keeping the application clean of
Kafka-specific concerns.

Note: publish_event.py already handles the no-Kafka fallback.
This file is the thin Kafka-specific wrapper used when Kafka IS enabled.
"""

from __future__ import annotations

import json

from app.core.logging import get_logger

log = get_logger("vision.kafka_publisher")

VISION_EVENTS_TOPIC = "vision.events"


class KafkaVisionPublisher:
    """
    Infrastructure adapter for publishing VisionEvents to Kafka.

    Wraps the shared ABHEDYA EventBus.  Injected into the application
    layer so tests can replace it with a fake.

    Usage
    ─────
        publisher = KafkaVisionPublisher()
        await publisher.publish(event_dict, key="CAM-PLANT-A-01")
    """

    def __init__(self, topic: str = VISION_EVENTS_TOPIC) -> None:
        self._topic = topic

    async def publish(self, payload: dict, key: str) -> None:
        """
        Publish a serialised VisionEvent payload to the Kafka topic.

        Parameters
        ──────────
        payload     Wire-format dict (from publish_event._serialize_event).
        key         Partition key (typically camera_id).

        Raises
        ──────
        KafkaPublishError  On Kafka broker failure.
        """
        try:
            from app.infrastructure.kafka.producer import EventBus  # late import

            bus = EventBus.get()
            await bus.publish(
                topic=self._topic,
                key=key,
                value=payload,
            )
            log.info(
                f"Published to topic={self._topic} "
                f"key={key} "
                f"event_id={payload.get('event_id', '?')}"
            )
        except Exception as exc:
            log.error(
                f"Kafka publish failed: topic={self._topic} "
                f"event_id={payload.get('event_id', '?')}: {exc}"
            )
            raise KafkaPublishError(str(exc)) from exc


class KafkaPublishError(Exception):
    """Raised when publishing to Kafka fails."""
