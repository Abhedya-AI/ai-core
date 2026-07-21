from datetime import datetime
from pydantic import Field, model_validator

from app.modules.knowledge.domain.entities.base import EventEntity
from app.modules.knowledge.domain.enums import PermitStatus


class Permit(EventEntity):
    """Work permit required for dangerous or restricted operations."""

    permit_type: str = "HOT_WORK"
    status: PermitStatus = PermitStatus.DRAFT
    issued_to_worker_id: str
    approved_by_worker_id: str | None = None
    zone_id: str
    equipment_id: str | None = None
    start_time: datetime
    end_time: datetime
    safety_checklist: list[str] = Field(default_factory=list)
    entity_type: str = Field(default="Permit")

    @model_validator(mode="after")
    def validate_permit_dates(self) -> "Permit":
        if self.end_time <= self.start_time:
            raise ValueError("Permit end_time must be after start_time")
        return self
