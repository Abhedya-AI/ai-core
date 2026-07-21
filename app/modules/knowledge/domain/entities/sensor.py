from pydantic import Field

from app.modules.knowledge.domain.entities.base import ObservationEntity
from app.modules.knowledge.domain.enums import SensorType


class Sensor(ObservationEntity):
    """IoT Telemetry sensor attached to equipment or zones."""

    sensor_type: SensorType = SensorType.TEMPERATURE
    unit: str = "C"
    min_threshold: float | None = None
    max_threshold: float | None = None
    sampling_interval_sec: int = Field(default=5)
    attached_equipment_id: str | None = None
    attached_zone_id: str | None = None
    entity_type: str = Field(default="Sensor")
