"""
application/use_cases/publish_event.py — PublishEventUseCase

Responsibility (ONE thing only)
────────────────────────────────
Publish a VisionEvent to the configured Kafka topic.

This use case knows nothing about:
  • Images or detectors     (→ AnalyzeFrameUseCase)
  • Risk calculation        (→ CalculateRiskUseCase)
  • Database                (→ SaveDetectionUseCase)

It answers exactly one question:
  "Has this VisionEvent been broadcast to downstream consumers?"

Design note
───────────
Publishing is best-effort. The orchestrator (ProcessDetectionUseCase)
catches EventPublishingError and logs a warning rather than failing the
entire pipeline. The event is already persisted at this point.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.application.exceptions import EventPublishingError
from app.modules.vision.application.publish_event import (
    PublishEventError,
    publish_vision_event,
)
from app.modules.vision.domain.entities import VisionEvent

log = get_logger("vision.use_cases.publish_event")


class PublishEventUseCase:
    """
    Publishes a VisionEvent to Kafka.

    No constructor dependencies — the Kafka producer is fetched from
    the EventBus singleton (or skipped when Kafka is disabled).

    Usage
    ─────
        await PublishEventUseCase().execute(event)
    """

    async def execute(self, event: VisionEvent) -> None:
        """
        Publish the VisionEvent.

        Raises
        ──────
        EventPublishingError  If the Kafka publish fails.
        """
        log.info(
            f"PublishEventUseCase: publishing event_id={event.event_id} "
            f"camera={event.camera_id} risk={event.risk_score.level.value}"
        )

        try:
            await publish_vision_event(event)
        except PublishEventError as exc:
            raise EventPublishingError(
                f"Kafka publish failed for event {event.event_id}: {exc}",
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise EventPublishingError(
                f"Unexpected publish error for event {event.event_id}: {exc}",
                detail=str(exc),
            ) from exc

        log.info(f"PublishEventUseCase: event {event.event_id} published ✓")
