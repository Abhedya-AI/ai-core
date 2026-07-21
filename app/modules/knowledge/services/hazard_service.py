"""hazard_service.py — Service managing Hazard identification and escalation."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.domain.entities.hazard import Hazard
from app.modules.knowledge.domain.rules import validate_hazard_escalation
from app.modules.knowledge.infrastructure.repositories.hazard_repository import HazardRepository

log = get_logger("knowledge.services.hazard")


class HazardService:
    """Domain service managing Hazard records, active risk conditions, and automatic escalation."""

    def __init__(self, repository: HazardRepository | None = None) -> None:
        self._repo = repository or HazardRepository()
        self._event_bus = EventBus.get()

    async def report_hazard(self, hazard: Hazard) -> dict[str, Any]:
        """Report a new hazard and trigger escalation if critical."""
        res = await self._repo.create_hazard(hazard)
        log.warning(f"Hazard Reported: [{hazard.severity}] '{hazard.title}' in Zone {hazard.zone_id}")

        await self._event_bus.publish(
            topic=Topics.RISK_THRESHOLD_BREACHED,
            payload={
                "hazard_id": hazard.id,
                "severity": hazard.severity.value,
                "zone_id": hazard.zone_id,
                "equipment_id": hazard.equipment_id,
            },
            key=hazard.id,
        )

        if validate_hazard_escalation(hazard):
            log.critical(f"CRITICAL UNMITIGATED HAZARD ESCALATION: {hazard.id}")
            await self._event_bus.publish(
                topic=Topics.EMERGENCY_ALERT_TRIGGERED,
                payload={"hazard_id": hazard.id, "severity": "CRITICAL", "zone_id": hazard.zone_id},
                key=hazard.id,
            )

        return res

    async def get_active_hazards(self) -> list[dict[str, Any]]:
        return await self._repo.get_active_hazards()

    async def get_critical_hazards(self) -> list[dict[str, Any]]:
        return await self._repo.get_critical_hazards()

    async def get_hazards_in_zone(self, zone_id: str) -> list[dict[str, Any]]:
        return await self._repo.get_hazards_in_zone(zone_id)
