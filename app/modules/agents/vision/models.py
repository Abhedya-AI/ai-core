"""models.py — Vision Intelligence Agent Domain Models & DTOs."""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.modules.agents.core.agent_result import AgentResult


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected objects."""

    x_min: float = 0.0
    y_min: float = 0.0
    x_max: float = 1.0
    y_max: float = 1.0


class VisionDetection(BaseModel):
    """Single visual object detection item."""

    label: str = Field(..., description="e.g. helmet, person, smoke, fire, oil_spill")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    bbox: BoundingBox = Field(default_factory=BoundingBox)
    track_id: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VisionConfidence(BaseModel):
    """Operational confidence calculated from multi-source fusion."""

    raw_model_confidence: float = 0.9
    tracker_consistency: float = 0.95
    multi_camera_agreement: float = 0.9
    sensor_agreement: float = 0.95
    operational_confidence: float = 0.93


class VisionEventPayload(BaseModel):
    """Standardized payload for vision domain events."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str = Field(default="CAM-01")
    frame_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    zone_id: str = Field(default="ZONE-A")
    event_type: str = Field(...)
    detections: list[dict[str, Any]] = Field(default_factory=list)
    confidence: VisionConfidence = Field(default_factory=VisionConfidence)
    image_reference: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VisionAgentResult(AgentResult):
    """Domain-extended result returned by Vision Intelligence Agent."""

    detected_events: list[VisionEventPayload] = Field(default_factory=list)
    visual_anomalies: list[str] = Field(default_factory=list)
    zone_occupancy: dict[str, Any] = Field(default_factory=dict)
    ppe_violations: list[str] = Field(default_factory=list)
    ocr_tags: list[str] = Field(default_factory=list)
