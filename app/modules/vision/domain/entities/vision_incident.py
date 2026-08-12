"""
domain/entities/vision_incident.py — VisionIncident domain entity.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.modules.vision.domain.entities.detection_event import AlertSeverity


class VisionIncident(BaseModel):
    """Lightweight incident candidate submitted from Vision to Incident Management."""

    model_config = ConfigDict(frozen=True)

    candidate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str
    zone_id: str | None = None
    plant_id: str | None = None
    incident_type: str
    severity: AlertSeverity
    detection_event_id: str
    alert_id: str | None = None
    description: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    is_submitted: bool = False

    def mark_submitted(self) -> "VisionIncident":
        return self.model_copy(update={"is_submitted": True})
