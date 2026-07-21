"""
kafka/consumer.py — BaseConsumer: abstract async Kafka consumer.

Subclass BaseConsumer to build domain-specific consumers.

Usage:
    class SensorConsumer(BaseConsumer):
        async def handle(self, topic: str, payload: dict, key: str) -> None:
            await sensor_service.process_reading(payload)

    consumer = SensorConsumer(topics=[Topics.SENSOR_READING_CREATED])
    await consumer.start()
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.kafka.registry import Topics

log = get_logger("kafka.consumer")


class BaseConsumer(ABC):
    """
    Abstract async Kafka consumer.

    Subclasses implement handle() to process incoming messages.
    The consumer loop runs in a background task.
    """

    def __init__(self, topics: list[str], group_id: str | None = None) -> None:
        self._topics = topics
        self._group_id = group_id or settings.kafka.consumer_group
        self._consumer = None
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the consumer background task."""
        if not settings.kafka.enabled:
            log.info(
                f"{self.__class__.__name__}: Kafka disabled, consumer not started"
            )
            return
        try:
            from aiokafka import AIOKafkaConsumer
            self._consumer = AIOKafkaConsumer(
                *self._topics,
                bootstrap_servers=settings.kafka.bootstrap_servers,
                group_id=self._group_id,
                client_id=f"{settings.kafka.client_id}-{self.__class__.__name__}",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            await self._consumer.start()
            self._running = True
            self._task = asyncio.create_task(self._consume_loop())
            log.info(
                f"{self.__class__.__name__} started → topics={self._topics}"
            )
        except Exception as exc:
            log.error(f"Failed to start {self.__class__.__name__}: {exc}")

    async def stop(self) -> None:
        """Stop the consumer and cancel the background task."""
        self._running = False
        if self._task:
            self._task.cancel()
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
        log.info(f"{self.__class__.__name__} stopped")

    async def _consume_loop(self) -> None:
        """Internal message loop."""
        while self._running and self._consumer:
            try:
                async for msg in self._consumer:
                    if not self._running:
                        break
                    try:
                        key = msg.key.decode("utf-8") if msg.key else None
                        await self.handle(
                            topic=msg.topic,
                            payload=msg.value,
                            key=key or "",
                        )
                    except Exception as exc:
                        log.error(
                            f"Error handling message from {msg.topic}: {exc}"
                        )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                log.error(f"Consumer loop error: {exc}")
                await asyncio.sleep(5)   # backoff before retry

    @abstractmethod
    async def handle(self, topic: str, payload: dict[str, Any], key: str) -> None:
        """
        Process a single message.

        Args:
            topic:   The Kafka topic the message came from.
            payload: Deserialized JSON payload.
            key:     Message key (empty string if not set).
        """
