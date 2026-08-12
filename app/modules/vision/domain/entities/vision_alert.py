"""
domain/entities/vision_alert.py — VisionAlert domain entity.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.modules.vision.domain.entities.detection_event import AlertSeverity


class AlertStatus(str, Enum):
    ACTIVE       = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED     = "RESOLVED"
    SUPPRESSED   = "SUPPRESSED"


class VisionAlert(BaseModel):
    """Consolidated alert generated from one or more detection events."""

    model_config = ConfigDict(frozen=True)

    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str
    zone_id: str | None = None
    plant_id: str | None = None
    alert_type: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    detection_ids: list[str] = Field(default_factory=list)
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return self.status == AlertStatus.ACTIVE

    @property
    def is_critical(self) -> bool:
        return self.severity == AlertSeverity.CRITICAL

    @property
    def age_seconds(self) -> float:
        return (datetime.now(tz=timezone.utc) - self.created_at).total_seconds()

    def acknowledge(self, user: str) -> "VisionAlert":
        return self.model_copy(update={"status": AlertStatus.ACKNOWLEDGED, "acknowledged_by": user, "acknowledged_at": datetime.now(tz=timezone.utc)})

    def resolve(self, user: str) -> "VisionAlert":
        return self.model_copy(update={"status": AlertStatus.RESOLVED, "resolved_by": user, "resolved_at": datetime.now(tz=timezone.utc)})

    def suppress(self) -> "VisionAlert":
        return self.model_copy(update={"status": AlertStatus.SUPPRESSED})
