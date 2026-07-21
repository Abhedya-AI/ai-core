"""permit_service.py — Service managing Work Permits and compliance validation."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.domain.entities.permit import Permit
from app.modules.knowledge.domain.enums import PermitStatus
from app.modules.knowledge.infrastructure.repositories.permit_repository import PermitRepository

log = get_logger("knowledge.services.permit")


class PermitService:
    """Domain service managing Work Permit issues, approvals, and activations."""

    def __init__(self, repository: PermitRepository | None = None) -> None:
        self._repo = repository or PermitRepository()
        self._event_bus = EventBus.get()

    async def issue_permit(self, permit: Permit) -> dict[str, Any]:
        """Issue a work permit."""
        res = await self._repo.create_permit(permit)
        log.info(f"Permit Issued: '{permit.title}' ({permit.permit_type}) in Zone {permit.zone_id}")
        await self._event_bus.publish(
            topic=Topics.GRAPH_NODE_CREATED,
            payload={"entity_type": "Permit", "id": permit.id, "status": permit.status.value},
            key=permit.id,
        )
        return res

    async def activate_permit(self, permit_id: str) -> bool:
        """Activate an approved permit."""
        updated = await self._repo.update_node(
            request=type("UpdateNodeRequest", (), {"node_id": permit_id, "label": "Permit", "properties": {"status": PermitStatus.ACTIVE.value}})()
        )
        if updated:
            log.info(f"Permit {permit_id} activated")
            await self._event_bus.publish(
                topic=Topics.GRAPH_NODE_CREATED,
                payload={"entity_type": "Permit", "id": permit_id, "status": "ACTIVE"},
                key=permit_id,
            )
            return True
        return False

    async def get_permits_in_zone(self, zone_id: str) -> list[dict[str, Any]]:
        return await self._repo.get_permits_in_zone(zone_id)

    async def get_active_permits_for_worker(self, worker_id: str) -> list[dict[str, Any]]:
        return await self._repo.get_active_permits_for_worker(worker_id)
