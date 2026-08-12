"""
events/vision_safety_events.py — Vision Safety Events Platform Definitions.

Events:
  - PPEViolationDetected
  - RestrictedZoneViolation
  - UnsafeBehaviorDetected
  - WorkerEquipmentInteractionDetected
  - WorkerFallDetected
  - FireConfirmed
  - SmokeConfirmed
  - CrowdCongestionDetected
  - OccupancyUpdated
  - VisionRecommendationGenerated
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus

log = get_logger("vision.events")


class VisionTopics:
    PPE_VIOLATION = "vision.ppe.violation"
    RESTRICTED_ZONE_VIOLATION = "vision.zone.violation"
    UNSAFE_BEHAVIOR = "vision.behavior.unsafe"
    EQUIPMENT_INTERACTION = "vision.interaction.equipment"
    WORKER_FALL = "vision.fall.detected"
    FIRE_CONFIRMED = "vision.fire.confirmed"
    SMOKE_CONFIRMED = "vision.smoke.confirmed"
    CROWD_CONGESTION = "vision.crowd.congestion"
    OCCUPANCY_UPDATED = "vision.occupancy.updated"
    RECOMMENDATION_GENERATED = "vision.recommendation.generated"


@dataclass
class BaseVisionEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_module: str = "vision_intelligence"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PPEViolationDetected(BaseVisionEvent):
    camera_id: str = ""
    zone_id: str = ""
    worker_id: str | None = None
    missing_ppe: list[str] = field(default_factory=list)
    compliance_score: float = 0.0
    risk_level: str = "HIGH"
    event_type: str = "PPEViolationDetected"


@dataclass
class RestrictedZoneViolation(BaseVisionEvent):
    camera_id: str = ""
    zone_id: str = ""
    worker_id: str | None = None
    violation_status: str = "UNAUTHORIZED_ENTRY"
    severity: str = "CRITICAL"
    event_type: str = "RestrictedZoneViolation"


@dataclass
class UnsafeBehaviorDetected(BaseVisionEvent):
    camera_id: str = ""
    zone_id: str = ""
    worker_id: str | None = None
    behavior_type: str = ""
    severity: str = "HIGH"
    confidence: float = 0.9
    event_type: str = "UnsafeBehaviorDetected"


@dataclass
class WorkerEquipmentInteractionDetected(BaseVisionEvent):
    camera_id: str = ""
    zone_id: str = ""
    worker_id: str = ""
    equipment_id: str = ""
    equipment_type: str = ""
    distance_meters: float = 0.0
    is_unsafe: bool = True
    event_type: str = "WorkerEquipmentInteractionDetected"


@dataclass
class WorkerFallDetected(BaseVisionEvent):
    camera_id: str = ""
    zone_id: str = ""
    worker_id: str = ""
    confidence: float = 0.95
    medical_emergency: bool = True
    event_type: str = "WorkerFallDetected"


@dataclass
class FireConfirmed(BaseVisionEvent):
    camera_id: str = ""
    zone_id: str = ""
    fused_confidence: float = 0.9
    temp_celsius: float | None = None
    event_type: str = "FireConfirmed"


@dataclass
class SmokeConfirmed(BaseVisionEvent):
    camera_id: str = ""
    zone_id: str = ""
    fused_confidence: float = 0.85
    event_type: str = "SmokeConfirmed"


@dataclass
class CrowdCongestionDetected(BaseVisionEvent):
    zone_id: str = ""
    worker_count: int = 0
    average_velocity: float = 0.0
    severity: str = "HIGH"
    event_type: str = "CrowdCongestionDetected"


@dataclass
class OccupancyUpdated(BaseVisionEvent):
    zone_id: str = ""
    worker_count: int = 0
    density_ratio: float = 0.0
    is_capacity_exceeded: bool = False
    event_type: str = "OccupancyUpdated"


@dataclass
class VisionRecommendationGenerated(BaseVisionEvent):
    recommendation_id: str = ""
    zone_id: str = ""
    title: str = ""
    priority: str = "HIGH"
    event_type: str = "VisionRecommendationGenerated"


async def publish_vision_event(event: BaseVisionEvent, topic: str) -> bool:
    """Publish vision safety event through EventBus."""
    try:
        payload = event.to_dict()
        key = getattr(event, "camera_id", None) or getattr(event, "zone_id", None) or event.event_id
        return await EventBus.get().publish(topic=topic, payload=payload, key=key)
    except Exception as exc:
        log.error(f"Failed to publish vision event {type(event).__name__}: {exc}")
        return False
