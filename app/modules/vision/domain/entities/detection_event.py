"""
domain/entities/detection_event.py — DetectionEvent domain aggregate.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.modules.vision.domain.enums.hazard_type import HazardType
from app.modules.vision.domain.enums.risk_level import RiskLevel
from app.modules.vision.domain.enums.stream_event_type import StreamEventType


class AlertSeverity(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


_HAZARD_TO_STREAM_EVENT: dict[HazardType, StreamEventType] = {
    HazardType.FIRE:                  StreamEventType.FIRE_DETECTED,
    HazardType.SMOKE:                 StreamEventType.SMOKE_DETECTED,
    HazardType.CHEMICAL_SPILL:        StreamEventType.FIRE_DETECTED,
    HazardType.FALL:                  StreamEventType.OBJECT_DETECTED,
    HazardType.RESTRICTED_ZONE_ENTRY: StreamEventType.RESTRICTED_ZONE_ENTRY,
    HazardType.FORKLIFT:              StreamEventType.EQUIPMENT_DETECTED,
    HazardType.CRANE:                 StreamEventType.EQUIPMENT_DETECTED,
    HazardType.TRUCK:                 StreamEventType.EQUIPMENT_DETECTED,
    HazardType.MACHINERY:             StreamEventType.EQUIPMENT_DETECTED,
    HazardType.PERSON:                StreamEventType.WORKER_DETECTED,
    HazardType.WORKER:                StreamEventType.WORKER_DETECTED,
}

_RISK_TO_SEVERITY: dict[RiskLevel, AlertSeverity] = {
    RiskLevel.CRITICAL: AlertSeverity.CRITICAL,
    RiskLevel.HIGH:     AlertSeverity.HIGH,
    RiskLevel.MEDIUM:   AlertSeverity.MEDIUM,
    RiskLevel.LOW:      AlertSeverity.LOW,
}


class DetectionEvent(BaseModel):
    """Integrates a Detection with its context for event publishing and KG sync."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    detection_id: str
    frame_id: str
    camera_id: str
    zone_id: str | None = None
    plant_id: str | None = None
    hazard_type: HazardType
    class_label: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    severity: AlertSeverity
    bounding_box: dict[str, Any] = Field(default_factory=dict)
    track_id: str | None = None
    is_ppe_violation: bool = False
    is_restricted_zone: bool = False
    is_critical: bool = False
    stream_event_type: StreamEventType = StreamEventType.OBJECT_DETECTED
    detected_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_detection(cls, detection: Any, frame_id: str, camera_id: str, zone_id: str | None, plant_id: str | None, track_id: str | None) -> "DetectionEvent":
        """Build a DetectionEvent from a Detection entity and context."""
        risk_level = detection.risk.level if detection.risk else RiskLevel.LOW
        risk_score = detection.risk.score if detection.risk else 0.0
        severity = _RISK_TO_SEVERITY.get(risk_level, AlertSeverity.LOW)
        stream_evt = _HAZARD_TO_STREAM_EVENT.get(detection.hazard_type, StreamEventType.OBJECT_DETECTED)
        is_ppe = detection.hazard_type.is_compliance_violation
        is_critical = severity in {AlertSeverity.HIGH, AlertSeverity.CRITICAL}
        return cls(
            detection_id=str(detection.id),
            frame_id=frame_id,
            camera_id=camera_id,
            zone_id=zone_id,
            plant_id=plant_id,
            hazard_type=detection.hazard_type,
            class_label=detection.hazard_type.value,
            confidence=detection.confidence,
            risk_score=float(risk_score),
            risk_level=risk_level,
            severity=severity,
            bounding_box={
                "x_min": detection.bounding_box.x_min,
                "y_min": detection.bounding_box.y_min,
                "x_max": detection.bounding_box.x_max,
                "y_max": detection.bounding_box.y_max,
            },
            track_id=track_id,
            is_ppe_violation=is_ppe,
            is_restricted_zone=detection.hazard_type == HazardType.RESTRICTED_ZONE_ENTRY,
            is_critical=is_critical,
            stream_event_type=stream_evt,
        )
