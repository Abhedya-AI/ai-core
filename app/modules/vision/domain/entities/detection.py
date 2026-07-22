from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    Domain representation of a detected hazard.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID

    camera_id: UUID

    hazard_type: HazardType

    confidence: float = Field(..., ge=0.0, le=1.0)

    bounding_box: BoundingBox

    risk: RiskScore

    status: DetectionStatus = DetectionStatus.PENDING

    detected_at: datetime

    @property
    def is_high_confidence(self) -> bool:
        """True if the model is highly certain of this detection (>= 0.75)."""
        return self.confidence >= 0.75

    @property
    def is_critical_hazard(self) -> bool:
        """True if the detected hazard is inherently critical."""
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
