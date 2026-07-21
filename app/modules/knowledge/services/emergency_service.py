"""emergency_service.py — Service managing Emergency response plans and active evacuations."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.domain.entities.emergency import EmergencyPlan
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("knowledge.services.emergency")


class EmergencyService:
    """Domain service managing active plant emergencies, evacuation plans, and responder dispatches."""

    def __init__(self, repository: BaseNeo4jRepository | None = None) -> None:
        self._repo = repository or BaseNeo4jRepository()
        self._event_bus = EventBus.get()

    async def trigger_emergency_plan(self, plan: EmergencyPlan) -> dict[str, Any]:
        """Trigger an active emergency response plan and alert responder teams."""
        props = plan.to_graph_properties()
        res = await self._repo.create_node(
            type("CreateNodeRequest", (), {"label": "EmergencyPlan", "node_id": plan.id, "properties": props})()
        )
        log.critical(f"EMERGENCY PLAN TRIGGERED: [{plan.emergency_type}] for Zones {plan.zone_ids}")

        await self._event_bus.publish(
            topic=Topics.EMERGENCY_ALERT_TRIGGERED,
            payload={
                "emergency_plan_id": plan.id,
                "emergency_type": plan.emergency_type,
                "zone_ids": plan.zone_ids,
            },
            key=plan.id,
        )
        return res

    async def dispatch_responders(self, plan_id: str, responder_ids: list[str]) -> bool:
        """Dispatch responders to an active emergency plan."""
        log.info(f"Dispatched responders {responder_ids} to emergency plan {plan_id}")
        return await self._event_bus.publish(
            topic=Topics.EMERGENCY_RESPONSE_DISPATCHED,
            payload={"emergency_plan_id": plan_id, "responder_ids": responder_ids},
            key=plan_id,
        )
