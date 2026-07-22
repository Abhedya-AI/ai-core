"""
api/serializers.py — Domain entity → response schema converters.

Responsibility: convert domain objects (Detection, Hazard, VisionEvent)
into Pydantic response schema instances.

Keeping this here (not in routes.py) means:
  • routes.py stays readable
  • serializers can be reused across multiple routes
  • changing the response schema only requires editing one file
"""

from __future__ import annotations

from app.modules.vision.domain.entities import Detection, Hazard, VisionEvent
from app.modules.vision.schemas.response import (
    BoundingBoxSchema,
    DetectionSchema,
    HazardSchema,
    RiskScoreSchema,
    VisionEventSchema,
)


def serialize_bounding_box(bb) -> BoundingBoxSchema:
    return BoundingBoxSchema(
        x_min=bb.x_min,
        y_min=bb.y_min,
        x_max=bb.x_max,
        y_max=bb.y_max,
    )


def serialize_detection(det: Detection) -> DetectionSchema:
    return DetectionSchema(
        id=det.id,
        hazard_type=det.hazard_type.value,
        status=det.status.value,
        confidence=det.confidence,
        bounding_box=serialize_bounding_box(det.bounding_box),
        frame_id=det.frame_id,
        camera_id=det.camera_id,
        timestamp=det.timestamp,
        image_path=det.image_path,
    )


def serialize_hazard(hazard: Hazard) -> HazardSchema:
    return HazardSchema(
        id=hazard.id,
        hazard_type=hazard.hazard_type.value,
        confidence=hazard.confidence,
        risk_level=hazard.risk_level.value,
        bounding_box=serialize_bounding_box(hazard.bounding_box),
        source_detection_ids=hazard.source_detection_ids,
        description=hazard.description,
        timestamp=hazard.timestamp,
        requires_immediate_action=hazard.requires_immediate_action,
    )


def serialize_risk_score(rs) -> RiskScoreSchema:
    return RiskScoreSchema(
        score=rs.score,
        level=rs.level.value,
        is_critical=rs.is_critical,
        reason=rs.reason,
    )


def serialize_vision_event(event: VisionEvent) -> VisionEventSchema:
    return VisionEventSchema(
        event_id=event.event_id,
        timestamp=event.timestamp,
        camera_id=event.camera_id,
        frame_id=event.frame_id,
        detection_count=event.detection_count,
        hazard_count=event.hazard_count,
        is_critical=event.is_critical,
        risk_score=serialize_risk_score(event.risk_score),
        detections=[serialize_detection(d) for d in event.detections],
        hazards=[serialize_hazard(h) for h in event.hazards],
        image_path=event.image_path,
        location=event.location,
        metadata=event.metadata,
    )
