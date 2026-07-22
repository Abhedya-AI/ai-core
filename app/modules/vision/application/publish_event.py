"""
application/publish_event.py — Kafka publish use-case.

Responsibility: serialise a VisionEvent and publish it to the
configured Kafka topic so downstream modules can react.

Design
──────
• The publisher uses the existing ABHEDYA Kafka EventBus
  (app.infrastructure.kafka.producer) when Kafka is enabled.
• If Kafka is disabled (settings.kafka.enabled = False), the event
  is logged as a structured dict and the use-case succeeds silently —
  useful for development and test environments.
• The Kafka message key is the camera_id so all events from the same
  camera land in the same partition (ordering guarantee).
• The published payload is a plain dict derived from the VisionEvent;
  it matches the Kafka event contract documented below.

Kafka Event Contract
────────────────────
Topic:  vision.events   (configurable via VISION_KAFKA_TOPIC env var)
Key:    camera_id
Value:
{
    "event_id":    str,
    "timestamp":   str (ISO-8601),
    "camera_id":   str,
    "frame_id":    str,
    "hazard_types": [str, ...],
    "risk_level":  str,
    "risk_value":  float,
    "location":    str | null,
    "detection_count": int,
    "hazard_count": int,
    "metadata":    {str: str}
}
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

    This is the published contract — downstream modules depend on these
    exact field names.  Any additive changes are backward-compatible;
    removals or renames require a versioning strategy.
    """
    return {
        "event_id":       event.event_id,
        "timestamp":      event.timestamp.isoformat(),
        "camera_id":      event.camera_id,
        "frame_id":       event.frame_id,
        "hazard_types":   [h.hazard_type.value for h in event.hazards],
        "risk_level":     event.risk_score.level.value,
        "risk_value":     event.risk_score.value,
        "location":       event.location,
        "detection_count": event.detection_count,
        "hazard_count":   event.hazard_count,
        "is_critical":    event.is_critical,
        "metadata":       event.metadata,
    }


# ── Use-case ──────────────────────────────────────────────────────────────────

class PublishEventError(Exception):
    """Raised when event publishing fails."""


async def publish_vision_event(event: VisionEvent) -> None:
    """
    Publish a VisionEvent to the Kafka topic.

    Falls back to structured logging if Kafka is disabled, so the
    use-case always succeeds in development environments.

    Parameters
    ──────────
    event   The domain aggregate to publish.

    Raises
    ──────
    PublishEventError  If Kafka is enabled but publishing fails.
    """
    payload = _serialize_event(event)

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
            key=event.camera_id,
            value=payload,
        )
        log.info(
            f"VisionEvent {event.event_id} published to "
            f"topic={VISION_KAFKA_TOPIC} key={event.camera_id}"
        )
    except Exception as exc:
        log.error(
            f"Failed to publish VisionEvent {event.event_id} "
            f"to {VISION_KAFKA_TOPIC}: {exc}"
        )
        raise PublishEventError(str(exc)) from exc
