"""
api/serializers.py — Domain entity → response schema converters.

Responsibility: convert domain objects (Camera, Detection, VisionEvent)
into Pydantic response schema instances.
"""

from __future__ import annotations

from app.modules.vision.domain.entities import Camera, Detection, VisionEvent
from app.modules.vision.schemas.response import (
    BoundingBoxSchema,
    CameraSchema,
    DetectionSchema,
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


def serialize_risk_score(rs) -> RiskScoreSchema:
    return RiskScoreSchema(
        score=rs.score,
        level=rs.level.value,
        reason=rs.reason,
    )


def serialize_camera(camera: Camera) -> CameraSchema:
    return CameraSchema(
        id=camera.id,
        name=camera.name,
        location=camera.location,
        is_active=camera.is_active,
        created_at=camera.created_at,
    )


def serialize_detection(det: Detection) -> DetectionSchema:
    return DetectionSchema(
        id=det.id,
        camera_id=det.camera_id,
        hazard_type=det.hazard_type.value,
        confidence=det.confidence,
        bounding_box=serialize_bounding_box(det.bounding_box),
        risk=serialize_risk_score(det.risk),
        status=det.status.value,
        detected_at=det.detected_at,
    )


def serialize_vision_event(event: VisionEvent) -> VisionEventSchema:
    return VisionEventSchema(
        event_id=event.event_id,
        detection_id=event.detection_id,
        camera_id=event.camera_id,
        hazard_type=event.hazard_type.value,
        risk_level=event.risk_level.value,
        confidence=event.confidence,
        occurred_at=event.occurred_at,
    )
