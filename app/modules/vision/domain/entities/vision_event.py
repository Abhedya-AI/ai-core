from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.vision.domain.enums import (
    HazardType,
    RiskLevel,
)


class VisionEvent(BaseModel):
    """
    Event published after successful hazard detection.
    """

    model_config = ConfigDict(frozen=True)

    event_id: UUID

    detection_id: UUID

    camera_id: UUID

    hazard_type: HazardType

    risk_level: RiskLevel

    confidence: float

    occurred_at: datetime
