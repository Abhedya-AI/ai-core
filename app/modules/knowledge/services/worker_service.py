"""worker_service.py — Service orchestrating Worker operations and event publishing."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.domain.entities.worker import Worker
from app.modules.knowledge.domain.entities.zone import Zone
from app.modules.knowledge.infrastructure.repositories.worker_repository import WorkerRepository
from app.modules.knowledge.services.validation_service import ValidationService

log = get_logger("knowledge.services.worker")


class WorkerService:
    """Domain service managing Worker lifecycle, zone assignments, and status events."""

    def __init__(self, repository: WorkerRepository | None = None) -> None:
        self._repo = repository or WorkerRepository()
        self._event_bus = EventBus.get()

    async def register_worker(self, worker: Worker) -> dict[str, Any]:
        """Register a new worker in the knowledge graph."""
        res = await self._repo.create_worker(worker)
        log.info(f"Registered Worker '{worker.name}' ({worker.badge_number})")
        await self._event_bus.publish(
            topic=Topics.WORKER_STATUS_UPDATED,
            payload={"worker_id": worker.id, "badge_number": worker.badge_number, "action": "REGISTERED"},
            key=worker.id,
        )
        return res

    async def assign_worker_to_zone(self, worker: Worker, zone: Zone) -> bool:
        """Assign worker to a zone after validating authorization policies."""
        ValidationService.validate_worker_zone_access(worker, zone)
        success = await self._repo.assign_zone(worker.id, zone.id)
        if success:
            log.info(f"Assigned Worker '{worker.badge_number}' to Zone '{zone.code}'")
            await self._event_bus.publish(
                topic=Topics.WORKER_STATUS_UPDATED,
                payload={"worker_id": worker.id, "zone_id": zone.id, "action": "ZONE_ASSIGNED"},
                key=worker.id,
            )
        return success

    async def get_worker_by_badge(self, badge_number: str) -> dict[str, Any] | None:
        return await self._repo.find_by_badge(badge_number)

    async def get_workers_in_zone(self, zone_id: str) -> list[dict[str, Any]]:
        return await self._repo.get_workers_in_zone(zone_id)
