"""maintenance_service.py — Service orchestrating Maintenance tasks and safety validations."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.domain.entities.maintenance import Maintenance
from app.modules.knowledge.domain.entities.permit import Permit
from app.modules.knowledge.domain.entities.zone import Zone
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.knowledge.services.validation_service import ValidationService

log = get_logger("knowledge.services.maintenance")


class MaintenanceService:
    """Domain service managing Maintenance task scheduling and execution safety validations."""

    def __init__(self, repository: BaseNeo4jRepository | None = None) -> None:
        self._repo = repository or BaseNeo4jRepository()
        self._event_bus = EventBus.get()

    async def schedule_maintenance(
        self,
        maintenance: Maintenance,
        permit: Permit | None = None,
        zone: Zone | None = None,
    ) -> dict[str, Any]:
        """Schedule a maintenance task after validating safety permit requirements for hazardous zones."""
        if zone:
            ValidationService.validate_permit_for_maintenance(maintenance, permit, zone)

        props = maintenance.to_graph_properties()
        res = await self._repo.create_node(
            type("CreateNodeRequest", (), {"label": "Maintenance", "node_id": maintenance.id, "properties": props})()
        )
        log.info(f"Scheduled Maintenance '{maintenance.title}' for Equipment {maintenance.equipment_id}")

        await self._event_bus.publish(
            topic=Topics.GRAPH_NODE_CREATED,
            payload={"entity_type": "Maintenance", "id": maintenance.id, "equipment_id": maintenance.equipment_id},
            key=maintenance.id,
        )
        return res

    async def get_maintenance_task(self, maintenance_id: str) -> dict[str, Any] | None:
        return await self._repo.find_by_id(maintenance_id)
