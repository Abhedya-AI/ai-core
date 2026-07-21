"""equipment_service.py — Service orchestrating Equipment operations and telemetry setup."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.domain.entities.equipment import Equipment
from app.modules.knowledge.domain.entities.sensor import Sensor
from app.modules.knowledge.infrastructure.repositories.equipment_repository import EquipmentRepository
from app.modules.knowledge.infrastructure.repositories.sensor_repository import SensorRepository
from app.modules.knowledge.services.validation_service import ValidationService

log = get_logger("knowledge.services.equipment")


class EquipmentService:
    """Domain service managing industrial equipment assets and attached telemetry sensors."""

    def __init__(
        self,
        equipment_repo: EquipmentRepository | None = None,
        sensor_repo: SensorRepository | None = None,
    ) -> None:
        self._equipment_repo = equipment_repo or EquipmentRepository()
        self._sensor_repo = sensor_repo or SensorRepository()
        self._event_bus = EventBus.get()

    async def register_equipment(self, equipment: Equipment) -> dict[str, Any]:
        """Register equipment asset in the knowledge graph."""
        res = await self._equipment_repo.create_equipment(equipment)
        log.info(f"Registered Equipment '{equipment.name}' ({equipment.code})")
        await self._event_bus.publish(
            topic=Topics.GRAPH_NODE_CREATED,
            payload={"entity_type": "Equipment", "id": equipment.id, "code": equipment.code},
            key=equipment.id,
        )
        return res

    async def attach_sensor_to_equipment(self, equipment_id: str, sensor: Sensor) -> bool:
        """Attach a telemetry sensor to equipment after validating threshold & duplicate policies."""
        ValidationService.validate_sensor_thresholds(sensor)
        existing = await self._sensor_repo.get_sensors_for_equipment(equipment_id)
        ValidationService.validate_no_duplicate_sensor_type(existing, sensor.sensor_type)

        # 1. Create sensor
        await self._sensor_repo.create_sensor(sensor)
        # 2. Attach to equipment
        success = await self._equipment_repo.attach_sensor(equipment_id, sensor.id)
        if success:
            log.info(f"Attached Sensor '{sensor.name}' ({sensor.sensor_type}) to Equipment '{equipment_id}'")
            await self._event_bus.publish(
                topic=Topics.GRAPH_RELATIONSHIP_CREATED,
                payload={
                    "rel_type": "HAS_SENSOR",
                    "source_id": equipment_id,
                    "target_id": sensor.id,
                },
                key=equipment_id,
            )
        return success

    async def get_equipment_in_zone(self, zone_id: str) -> list[dict[str, Any]]:
        return await self._equipment_repo.get_equipment_in_zone(zone_id)

    async def get_maintenance_history(self, equipment_id: str) -> list[dict[str, Any]]:
        return await self._equipment_repo.get_maintenance_history(equipment_id)
