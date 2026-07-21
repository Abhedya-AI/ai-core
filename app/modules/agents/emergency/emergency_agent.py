"""emergency_agent.py — Emergency Agent planning evacuations and response actions."""

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent


class EmergencyAgent(BaseAgent):
    """Specialized agent formulating structured emergency evacuation and isolation plans."""

    name: str = "EmergencyAgent"
    description: str = "Generates evacuation routes, isolation procedures, and emergency plans."

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        zone_id = context.zone_id or "ZONE-B"
        actions = [
            f"Initiate immediate siren evacuation for {zone_id}",
            "Isolate upstream fuel valve V-4",
            "Notify Shift Supervisor and Fire Response Team",
        ]

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=0.99,
            evidence=[f"Activated Emergency Plan EP-03 for {zone_id}"],
            recommendations=actions,
            events=[{"topic": "EMERGENCY_ALERT_TRIGGERED", "payload": {"zone_id": zone_id, "plan": "EP-03"}}],
            output_data={"zone_id": zone_id, "emergency_plan": "EP-03", "actions": actions},
            explanation=f"Emergency Agent generated actionable response plan EP-03 for '{zone_id}'.",
        )
