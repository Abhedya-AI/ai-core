from pydantic import Field

from app.modules.knowledge.domain.entities.base import EventEntity


class Weather(EventEntity):
    """Environmental/weather condition observation for open-air zones."""

    temperature_c: float
    humidity_pct: float
    wind_speed_kmh: float
    condition: str = "CLEAR"
    zone_id: str | None = None
    entity_type: str = Field(default="Weather")
