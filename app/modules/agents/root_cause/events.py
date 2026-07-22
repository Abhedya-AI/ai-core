"""events.py — Standardized Root Cause Domain Event Generator."""

from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.root_cause.models import Hypothesis


class RootCauseEventGenerator:
    """Generates standardized root cause domain events for the EventBus."""

    @staticmethod
    def generate_events(
        agent_name: str,
        incident_id: str,
        primary_hypothesis: Hypothesis,
        actions: list[str],
        trace_id: str,
    ) -> list[AgentDomainEvent]:
        """
        Generate domain events.

        Returns:
            list of AgentDomainEvent objects (RootCauseIdentified, CorrectiveActionRecommended, InvestigationCompleted).
        """
        return [
            AgentDomainEvent(
                event_type="RootCauseIdentified",
                agent_name=agent_name,
                payload={
                    "incident_id": incident_id,
                    "root_cause": primary_hypothesis.root_cause_candidate,
                    "confidence": primary_hypothesis.confidence_score,
                    "causal_path": primary_hypothesis.causal_path,
                },
                trace_id=trace_id,
            ),
            AgentDomainEvent(
                event_type="CorrectiveActionRecommended",
                agent_name=agent_name,
                payload={
                    "incident_id": incident_id,
                    "recommended_actions": actions[:3],
                },
                trace_id=trace_id,
            ),
            AgentDomainEvent(
                event_type="InvestigationCompleted",
                agent_name=agent_name,
                payload={"incident_id": incident_id, "primary_hypothesis": primary_hypothesis.model_dump()},
                trace_id=trace_id,
            ),
        ]
