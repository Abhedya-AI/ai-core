"""events.py — Standardized Emergency Domain Event Generator."""

from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.emergency.models import EmergencyPlan


class EmergencyEventGenerator:
    """Generates standardized emergency domain events for the EventBus."""

    @staticmethod
    def generate_events(
        agent_name: str,
        plan: EmergencyPlan,
        trace_id: str,
    ) -> list[AgentDomainEvent]:
        """
        Generate emergency domain events.

        Returns:
            list of AgentDomainEvent objects (EmergencyPlanGenerated, EvacuationInitiated, ResourceAllocated, ResponderDispatched).
        """
        events: list[AgentDomainEvent] = [
            AgentDomainEvent(
                event_type="EmergencyPlanGenerated",
                agent_name=agent_name,
                payload={"plan_id": plan.plan_id, "target_zone": plan.target_zone, "action_count": len(plan.actions)},
                trace_id=trace_id,
            )
        ]

        if plan.evacuation_routes:
            events.append(
                AgentDomainEvent(
                    event_type="EvacuationInitiated",
                    agent_name=agent_name,
                    payload={"zone_id": plan.target_zone, "exit": plan.evacuation_routes[0].recommended_exit},
                    trace_id=trace_id,
                )
            )

        for res in plan.resource_assignments:
            events.append(
                AgentDomainEvent(
                    event_type="ResourceAllocated",
                    agent_name=agent_name,
                    payload=res.model_dump(),
                    trace_id=trace_id,
                )
            )
            events.append(
                AgentDomainEvent(
                    event_type="ResponderDispatched",
                    agent_name=agent_name,
                    payload={"resource_id": res.resource_id, "assigned_zone": res.assigned_zone},
                    trace_id=trace_id,
                )
            )

        return events
