"""sensor_service.py — Service managing Sensor devices and readings."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.domain.entities.sensor import Sensor
from app.modules.knowledge.infrastructure.repositories.sensor_repository import SensorRepository
from app.modules.knowledge.services.validation_service import ValidationService

log = get_logger("knowledge.services.sensor")


class SensorService:
    """Domain service managing IoT sensor devices and telemetry ingestion events."""

    def __init__(self, repository: SensorRepository | None = None) -> None:
        self._repo = repository or SensorRepository()
        self._event_bus = EventBus.get()

    async def register_sensor(self, sensor: Sensor) -> dict[str, Any]:
        """Register a new sensor device."""
        ValidationService.validate_sensor_thresholds(sensor)
        res = await self._repo.create_sensor(sensor)
        log.info(f"Registered Sensor '{sensor.name}' ({sensor.sensor_type})")
        await self._event_bus.publish(
            topic=Topics.GRAPH_NODE_CREATED,
            payload={"entity_type": "Sensor", "id": sensor.id, "sensor_type": sensor.sensor_type.value},
            key=sensor.id,
        )
        return res

    async def record_sensor_reading(self, sensor_id: str, value: float, timestamp: str | None = None) -> bool:
        """Record a telemetry reading and publish SENSOR_READING_CREATED event."""
        log.debug(f"Telemetry reading on {sensor_id}: {value}")
        return await self._event_bus.publish(
            topic=Topics.SENSOR_READING_CREATED,
            payload={"sensor_id": sensor_id, "value": value, "timestamp": timestamp},
            key=sensor_id,
        )

    async def get_sensors_for_equipment(self, equipment_id: str) -> list[dict[str, Any]]:
        return await self._repo.get_sensors_for_equipment(equipment_id)
