from pydantic import Field

from app.modules.knowledge.domain.entities.base import EventEntity
from app.modules.knowledge.domain.enums import HazardLevel


class Hazard(EventEntity):
    """Identified safety hazard or risk condition."""

    severity: HazardLevel = HazardLevel.MEDIUM
    description: str
    detected_by_sensor_id: str | None = None
    detected_by_camera_id: str | None = None
    zone_id: str
    equipment_id: str | None = None
    mitigated: bool = False
    entity_type: str = Field(default="Hazard")
