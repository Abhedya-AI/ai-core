from pydantic import Field

from app.modules.knowledge.domain.entities.base import EventEntity
from app.modules.knowledge.domain.enums import IncidentStatus


class Incident(EventEntity):
    """Safety incident or near-miss event."""

    status: IncidentStatus = IncidentStatus.OPEN
    description: str
    originating_hazard_id: str | None = None
    zone_id: str
    equipment_id: str | None = None
    affected_worker_ids: list[str] = Field(default_factory=list)
    root_cause_summary: str | None = None
    entity_type: str = Field(default="Incident")
