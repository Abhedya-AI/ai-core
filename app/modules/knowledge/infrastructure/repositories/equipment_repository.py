"""equipment_repository.py — Domain repository for Equipment operations."""

from typing import Any

from app.modules.knowledge.domain.entities.equipment import Equipment
from app.modules.knowledge.infrastructure.cypher import equipment as cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository


class EquipmentRepository(BaseNeo4jRepository):
    """Domain repository for Equipment operations."""

    async def create_equipment(self, equipment: Equipment) -> dict[str, Any]:
        """Create or merge Equipment node."""
        props = equipment.to_graph_properties()
        records = await self.execute_query(
            cypher.CREATE_EQUIPMENT,
            {
                "id": equipment.id,
                "code": equipment.code,
                "properties": props,
            },
        )
        return records[0].get("e", props) if records else props

    async def get_equipment_in_zone(self, zone_id: str) -> list[dict[str, Any]]:
        """Fetch all equipment located in a given zone."""
        records = await self.execute_query(cypher.EQUIPMENT_IN_ZONE, {"zone_id": zone_id})
        return [dict(r["e"]._properties) if hasattr(r["e"], "_properties") else dict(r["e"]) for r in records if "e" in r]

    async def attach_sensor(self, equipment_id: str, sensor_id: str) -> bool:
        """Create a HAS_SENSOR relationship from Equipment to Sensor."""
        records = await self.execute_query(
            cypher.ATTACH_SENSOR_TO_EQUIPMENT,
            {"equipment_id": equipment_id, "sensor_id": sensor_id},
        )
        return bool(records)

    async def get_maintenance_history(self, equipment_id: str) -> list[dict[str, Any]]:
        """Retrieve maintenance history records for an equipment."""
        records = await self.execute_query(
            cypher.GET_EQUIPMENT_MAINTENANCE_HISTORY,
            {"equipment_id": equipment_id},
        )
        return [dict(r["m"]._properties) if hasattr(r["m"], "_properties") else dict(r["m"]) for r in records if "m" in r]
