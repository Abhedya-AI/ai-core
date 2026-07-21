from pydantic import Field

from app.modules.knowledge.domain.entities.base import LocationEntity


class Building(LocationEntity):
    """Building structure within an industrial facility."""

    plant_code: str
    total_floors: int = Field(default=1)
    entity_type: str = Field(default="Building")
