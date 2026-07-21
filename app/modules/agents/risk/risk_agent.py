"""risk_agent.py — Risk Agent specializing in hazard scoring and risk propagation."""

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.types import Capability
from app.modules.knowledge.graph_intelligence import IntelligenceService


class RiskAgent(BaseAgent):
    """Specialized agent for hazard scoring, risk propagation, and critical asset detection."""

    name: str = "RiskAgent"
    version: str = "1.0.0"
    description: str = "Calculates hazard severity, risk propagation, and worker exposure."
    capabilities: list[Capability] = [Capability.RISK_ANALYSIS, Capability.GRAPH_SEARCH]

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        hazard_id = context.target_entity_id or "HAZ-MAIN"
        graph_adj = context.graph_snapshot or {hazard_id: ["EQUIPMENT-1", "ZONE-A"]}

        report = IntelligenceService.analyze_risk_propagation(hazard_id, graph_adj, initial_risk=90.0)

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=report.intelligence_result.confidence,
            evidence=report.intelligence_result.evidence,
            recommendations=["Isolate high-risk equipment immediately", "Verify worker evacuation status in affected radius"],
            output_data={
                "max_risk": report.max_risk_score,
                "affected_nodes": report.affected_node_ids,
                "scores": report.propagated_risk_scores,
            },
            explanation=report.intelligence_result.explanation,
        )
