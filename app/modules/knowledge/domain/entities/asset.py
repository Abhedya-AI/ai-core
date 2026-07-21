from pydantic import Field

from app.modules.knowledge.domain.entities.base import AssetEntity
from app.modules.knowledge.domain.enums import EquipmentStatus


class Asset(AssetEntity):
    """Generic industrial asset."""

    category: str = Field(default="GENERAL")
    status: EquipmentStatus = EquipmentStatus.OPERATIONAL
    criticality: str = Field(default="MEDIUM")
    entity_type: str = Field(default="Asset")
