"""
application/publish_event.py — Kafka publish use-case.

Responsibility: serialise a VisionEvent and publish it to the
configured Kafka topic so downstream modules can react.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.vision.domain.entities import VisionEvent

log = get_logger("vision.publish_event")

# ── Constants ─────────────────────────────────────────────────────────────────
VISION_KAFKA_TOPIC = "vision.events"


# ── Serialisation ─────────────────────────────────────────────────────────────

def _serialize_event(event: VisionEvent) -> dict:
    """
    Convert a VisionEvent into the Kafka wire-format dict.
    """
    return {
        "event_id":         event.event_id,
        "camera_id":        event.camera_id,
        "frame_id":         event.frame_id,
        "risk_level":       event.risk_score.level.value,
        "risk_score":       event.risk_score.score,
        "risk_reason":      event.risk_score.reason,
        "detection_count":  event.detection_count,
        "hazard_count":     event.hazard_count,
        "is_critical":      event.is_critical,
        "hazard_types":     [h.hazard_type.value for h in event.hazards],
        "occurred_at":      event.occurred_at.isoformat(),
    }


# ── Use-case ──────────────────────────────────────────────────────────────────

class PublishEventError(Exception):
    """Raised when event publishing fails."""
    pass


async def publish_vision_event(event: VisionEvent) -> None:
    """
    Publish a VisionEvent to the Kafka topic.
    """
    payload = _serialize_event(event)
    key_str = str(event.camera_id)

    if not settings.kafka.enabled:
        log.info(
            f"Kafka disabled — event logged locally: "
            f"topic={VISION_KAFKA_TOPIC} "
            f"event_id={event.event_id} "
            f"payload={json.dumps(payload)}"
        )
        return

    try:
        from app.infrastructure.kafka.producer import EventBus  # late import

        bus = EventBus.get()
        await bus.publish(
            topic=VISION_KAFKA_TOPIC,
            key=key_str,
            value=payload,
        )
        log.info(
            f"VisionEvent {event.event_id} published to "
            f"topic={VISION_KAFKA_TOPIC} key={key_str}"
        )
    except Exception as exc:
        log.error(
            f"Failed to publish VisionEvent {event.event_id} "
            f"to {VISION_KAFKA_TOPIC}: {exc}"
        )
        raise PublishEventError(str(exc)) from exc
