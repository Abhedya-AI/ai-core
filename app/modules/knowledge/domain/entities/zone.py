from pydantic import Field

from app.modules.knowledge.domain.entities.base import LocationEntity
from app.modules.knowledge.domain.enums import ZoneType


class Zone(LocationEntity):
    """Specific zone or area within a plant floor."""

    zone_type: ZoneType = ZoneType.PROCESSING
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    max_capacity: int = Field(default=50)
    is_active: bool = True
    entity_type: str = Field(default="Zone")
