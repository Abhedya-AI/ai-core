"""
domain/entities/vision_event.py — VisionEvent aggregate root.

VisionEvent is the main output of the Vision Intelligence module.
It aggregates all detections for a single frame and holds the computed
risk score and the list of actionable hazards.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.modules.vision.domain.enums import (
    HazardType,
    RiskLevel,
)
from app.modules.vision.domain.value_objects import RiskScore


class VisionEvent(BaseModel):
    """
    Aggregate root produced after a full frame analysis.

    Fields
    ──────
    event_id     Auto-generated UUID.
    camera_id    Source camera identifier.
    frame_id     Source frame identifier.
    detections   All Detection objects found in this frame.
    hazards      Deduped, actionable Hazard list from the RiskEngine.
    risk_score   Aggregated RiskScore for the frame.
    occurred_at  UTC timestamp (auto-set on creation).
    """

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    camera_id: str

    frame_id: str

    # Circular import avoided by using forward reference + TYPE_CHECKING
    detections: List = Field(default_factory=list)

    hazards: List = Field(default_factory=list)

    risk_score: RiskScore

    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def detection_count(self) -> int:
        return len(self.detections)

    @property
    def hazard_count(self) -> int:
        return len(self.hazards)

    @property
    def is_critical(self) -> bool:
        return self.risk_score.level == RiskLevel.CRITICAL

    @property
    def unique_hazard_types(self) -> set[HazardType]:
        """Set of unique HazardType values across all hazards."""
        return {h.hazard_type for h in self.hazards}

    @property
    def actionable_hazards(self) -> list:
        """Hazards with non-zero risk weight (compliant items excluded)."""
        return [h for h in self.hazards if h.weight > 0.0]

    def summary(self) -> str:
        """Single-line human-readable summary of this event."""
        return (
            f"VisionEvent[{self.event_id[:8]}] "
            f"camera={self.camera_id} "
            f"frame={self.frame_id} "
            f"risk={self.risk_score.level.value} "
            f"score={self.risk_score.score:.2f} "
            f"detections={self.detection_count}"
        )
