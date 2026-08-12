"""
domain/entities/detection.py — Detection domain entity.

A Detection represents a single hazard identified in a camera frame.
It is immutable by default (frozen Pydantic model).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.vision.domain.enums import (
    DetectionStatus,
    HazardType,
)
from app.modules.vision.domain.value_objects import (
    BoundingBox,
    RiskScore,
)


class Detection(BaseModel):
    """
    Domain representation of a single detected hazard in a camera frame.

    Fields
    ──────
    id           Auto-generated UUID (unique detection identity).
    hazard_type  The type of hazard detected.
    confidence   Model confidence score in [0.0, 1.0].
    bounding_box Normalised bounding box of the detected object.
    frame_id     Identifier of the source frame (string).
    camera_id    Identifier of the source camera (string).
    risk         Optional pre-computed RiskScore (set after risk calculation).
    status       Lifecycle state — defaults to PENDING.
    detected_at  UTC timestamp of detection (auto-set).
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    hazard_type: HazardType

    confidence: float = Field(..., ge=0.0, le=1.0)

    bounding_box: BoundingBox

    frame_id: str

    camera_id: str

    risk: Optional[RiskScore] = None

    status: DetectionStatus = DetectionStatus.PENDING

    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def is_high_confidence(self) -> bool:
        """True if model confidence ≥ 0.75."""
        return self.confidence >= 0.75

    @property
    def is_critical_hazard(self) -> bool:
        """True if this hazard type is inherently critical."""
        return self.hazard_type in {
            HazardType.FIRE,
            HazardType.CHEMICAL_SPILL,
            HazardType.FALL,
        }

    @property
    def is_pending(self) -> bool:
        return self.status == DetectionStatus.PENDING

    @property
    def is_verified(self) -> bool:
        return self.status == DetectionStatus.VERIFIED

    # ── State transitions (return new instances — entity is frozen) ────────────

    def verify(self) -> "Detection":
        """Return a new Detection with status VERIFIED."""
        return self.model_copy(update={"status": DetectionStatus.VERIFIED})

    def reject(self) -> "Detection":
        """Return a new Detection with status REJECTED."""
        return self.model_copy(update={"status": DetectionStatus.REJECTED})
