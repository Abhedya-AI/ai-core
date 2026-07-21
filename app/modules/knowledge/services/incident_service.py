"""incident_service.py — Service managing Incident reporting and investigation timelines."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.domain.entities.incident import Incident
from app.modules.knowledge.infrastructure.repositories.incident_repository import IncidentRepository

log = get_logger("knowledge.services.incident")


class IncidentService:
    """Domain service managing Incident lifecycles and root cause investigation context."""

    def __init__(self, repository: IncidentRepository | None = None) -> None:
        self._repo = repository or IncidentRepository()
        self._event_bus = EventBus.get()

    async def report_incident(self, incident: Incident) -> dict[str, Any]:
        """Report a safety incident and notify emergency services."""
        res = await self._repo.create_incident(incident)
        log.error(f"INCIDENT REPORTED: [{incident.status}] '{incident.title}' in Zone {incident.zone_id}")
        await self._event_bus.publish(
            topic=Topics.EMERGENCY_ALERT_TRIGGERED,
            payload={
                "incident_id": incident.id,
                "status": incident.status.value,
                "zone_id": incident.zone_id,
                "originating_hazard_id": incident.originating_hazard_id,
            },
            key=incident.id,
        )
        return res

    async def get_incident_timeline(self, incident_id: str) -> dict[str, Any] | None:
        return await self._repo.get_incident_timeline(incident_id)

    async def get_affected_workers(self, incident_id: str) -> list[dict[str, Any]]:
        return await self._repo.get_affected_workers(incident_id)
