from datetime import datetime
from pydantic import Field

from app.modules.knowledge.domain.entities.base import AssetEntity
from app.modules.knowledge.domain.enums import EquipmentStatus


class Equipment(AssetEntity):
    """Specific machine, pump, valve, motor, tank, or pipeline."""

    model_number: str | None = None
    serial_number: str | None = None
    status: EquipmentStatus = EquipmentStatus.OPERATIONAL
    zone_id: str | None = None
    last_serviced: datetime | None = None
    health_score: float = Field(default=100.0, ge=0.0, le=100.0)
    entity_type: str = Field(default="Equipment")
