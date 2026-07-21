"""sensor_repository.py — Domain repository for Sensor operations."""

from typing import Any

from app.modules.knowledge.domain.entities.sensor import Sensor
from app.modules.knowledge.infrastructure.cypher import sensors as cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository


class SensorRepository(BaseNeo4jRepository):
    """Domain repository for Sensor operations."""

    async def create_sensor(self, sensor: Sensor) -> dict[str, Any]:
        """Create or merge a Sensor node."""
        props = sensor.to_graph_properties()
        records = await self.execute_query(
            cypher.CREATE_SENSOR,
            {"id": sensor.id, "properties": props},
        )
        return records[0].get("s", props) if records else props

    async def get_sensors_for_equipment(self, equipment_id: str) -> list[dict[str, Any]]:
        """Fetch all sensors attached to an equipment."""
        records = await self.execute_query(cypher.SENSORS_FOR_EQUIPMENT, {"equipment_id": equipment_id})
        return [dict(r["s"]._properties) if hasattr(r["s"], "_properties") else dict(r["s"]) for r in records if "s" in r]
