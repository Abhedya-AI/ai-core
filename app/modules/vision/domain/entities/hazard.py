"""
domain/entities/hazard.py — Hazard value object.

A Hazard is an actionable, deduped representation of a detected hazard type
within a VisionEvent. The RiskEngine produces one Hazard per unique HazardType
it finds across all detections in a frame.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.vision.domain.enums import HazardType


class Hazard(BaseModel):
    """
    A single actionable hazard surfaced in a VisionEvent.

    Attributes
    ──────────
    hazard_type     The type of hazard identified.
    weight          Risk weight of this hazard (0.0 – 1.0).
    description     Human-readable description of the risk.
    max_confidence  Highest confidence score across all detections of this type.
    """

    model_config = ConfigDict(frozen=True)

    hazard_type:     HazardType
    weight:          float
    description:     str
    max_confidence:  float = 0.0

    @property
    def is_critical(self) -> bool:
        """True if this hazard alone qualifies as CRITICAL risk."""
        return self.weight >= 0.75

    def __repr__(self) -> str:
        return (
            f"Hazard(type={self.hazard_type.value}, "
            f"weight={self.weight:.2f}, "
            f"conf={self.max_confidence:.2f})"
        )
