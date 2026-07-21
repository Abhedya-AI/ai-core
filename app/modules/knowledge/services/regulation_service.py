"""regulation_service.py — Service managing Safety Regulations and regulatory compliance."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.domain.entities.regulation import Regulation
from app.modules.knowledge.infrastructure.repositories.regulation_repository import RegulationRepository

log = get_logger("knowledge.services.regulation")


class RegulationService:
    """Domain service managing OSHA/ISO safety regulations and hazard linkages."""

    def __init__(self, repository: RegulationRepository | None = None) -> None:
        self._repo = repository or RegulationRepository()
        self._event_bus = EventBus.get()

    async def register_regulation(self, regulation: Regulation) -> dict[str, Any]:
        """Register a new safety regulation."""
        res = await self._repo.create_regulation(regulation)
        log.info(f"Registered Regulation '{regulation.code}' — {regulation.title}")
        await self._event_bus.publish(
            topic=Topics.GRAPH_NODE_CREATED,
            payload={"entity_type": "Regulation", "id": regulation.id, "code": regulation.code},
            key=regulation.id,
        )
        return res

    async def get_regulations_for_hazard(self, hazard_id: str) -> list[dict[str, Any]]:
        return await self._repo.get_regulations_for_hazard(hazard_id)
