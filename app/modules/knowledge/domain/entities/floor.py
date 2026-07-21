from pydantic import Field

from app.modules.knowledge.domain.entities.base import LocationEntity


class Floor(LocationEntity):
    """Floor level inside a building."""

    building_id: str
    level_number: int
    entity_type: str = Field(default="Floor")
