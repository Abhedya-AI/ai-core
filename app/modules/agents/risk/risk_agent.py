"""
risk_agent.py — Master Risk Intelligence Agent.

Autonomous reasoning system orchestrating evidence gathering, deterministic scoring,
graph risk propagation, XAI explanation, categorized recommendations, and event publishing.
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.core.types import Capability
from app.modules.agents.risk.analyzer import RiskAnalyzer
from app.modules.agents.risk.explanation import RiskExplanationGenerator
from app.modules.agents.risk.models import RiskAgentResult
from app.modules.agents.risk.policies import evaluate_risk_policy
from app.modules.agents.risk.propagation import RiskPropagationEngine
from app.modules.agents.risk.recommendation import RiskRecommendationEngine
from app.modules.agents.risk.scorer import RiskScorer

log = get_logger("agents.risk.orchestrator")


class RiskAgent(BaseAgent):
    """
    Master Risk Intelligence Agent.

    Orchestrates:
      Context -> Analyzer -> Scorer -> Propagation -> Explanation -> Recommendation -> Policies & Events.
    """

    name: str = "RiskAgent"
    version: str = "1.0.0"
    description: str = "Calculates hazard severity, risk propagation, and worker exposure."
    capabilities: list[Capability] = [Capability.RISK_ANALYSIS, Capability.GRAPH_SEARCH]

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        target_id = context.target_entity_id or "HAZ-MAIN"

        # 1. Gather Evidence
        evidence = RiskAnalyzer.gather_evidence(context)

        # 2. Compute Deterministic Risk Score
        score = RiskScorer.compute_score(evidence, target_id=target_id)

        # 3. Propagate Risk via Graph Intelligence Engine
        graph_adj = context.graph_snapshot or {target_id: ["EQUIPMENT-1", "ZONE-A"]}
        affected_nodes, prop_scores = RiskPropagationEngine.propagate(target_id, graph_adj, initial_risk=score.score_value)

        # 4. Generate Grounded XAI Explanation
        explanation = RiskExplanationGenerator.generate_explanation(target_id, score, evidence, affected_nodes)

        # 5. Generate Categorized Recommendations
        recs_list, recs_dict = RiskRecommendationEngine.generate_recommendations(target_id, score, affected_nodes)

        # 6. Evaluate Business Rules & Formulate Events
        policy_eval = evaluate_risk_policy(score, hazard_type=context.query)
        events: list[AgentDomainEvent] = [
            AgentDomainEvent(
                event_type=policy_eval["event_type"],
                agent_name=self.name,
                payload={
                    "asset": target_id,
                    "severity": score.severity.value,
                    "score": score.score_value,
                    "affected_entities": affected_nodes,
                },
                trace_id=context.trace_id,
            )
        ]

        if policy_eval["trigger_emergency"]:
            events.append(
                AgentDomainEvent(
                    event_type="EmergencyTriggerRequested",
                    agent_name=self.name,
                    payload={
                        "asset": target_id,
                        "zone_id": context.zone_id or "ZONE-A",
                        "reason": f"Critical risk score {score.score_value} on {target_id}",
                    },
                    trace_id=context.trace_id,
                )
            )

        evidence_summaries = [f"Deterministic risk impact score: {score.score_value}/100"]
        if evidence.sensor_readings:
            evidence_summaries.append(f"Analyzed {len(evidence.sensor_readings)} sensor reading(s)")

        return RiskAgentResult(
            agent_name=self.name,
            success=True,
            confidence=score.confidence,
            evidence=evidence_summaries,
            recommendations=recs_list,
            categorized_recommendations=recs_dict,
            events=events,
            risk_score=score,
            severity=score.severity,
            affected_entities=affected_nodes,
            propagation_paths=[{"start": target_id, "scores": prop_scores}],
            output_data={
                "target_id": target_id,
                "score": score.model_dump(),
                "affected_nodes": affected_nodes,
                "categorized_recommendations": recs_dict,
            },
            explanation=explanation,
        )
