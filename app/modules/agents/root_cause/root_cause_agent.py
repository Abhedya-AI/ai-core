"""root_cause_agent.py — Root Cause Analysis Agent."""

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.knowledge.graph_intelligence import IntelligenceService


class RootCauseAgent(BaseAgent):
    """Specialized agent performing root cause discovery and causal chain reconstruction."""

    name: str = "RootCauseAgent"
    description: str = "Reconstructs causal failure chains and discovers root causes."

    async def can_handle(self, context: AgentContext) -> bool:
        return "incident" in context.query.lower() or "cause" in context.query.lower()

    async def _run(self, context: AgentContext) -> AgentResult:
        incident_id = context.target_entity_id or "INC-01"
        incoming = context.graph_snapshot or {
            incident_id: ["HAZ-LEAK"],
            "HAZ-LEAK": ["VALVE-FAIL"],
            "VALVE-FAIL": ["SENSOR-FAULT"],
        }

        report = IntelligenceService.analyze_incident(incident_id, incoming)

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=report.intelligence_result.confidence,
            evidence=report.intelligence_result.evidence,
            recommendations=["Replace faulty telemetry sensor SENSOR-FAULT", "Recalibrate pressure relief valve"],
            output_data={
                "incident_id": incident_id,
                "root_causes": report.candidate_root_causes,
                "causal_path": report.causal_path,
            },
            explanation=report.intelligence_result.explanation,
        )
