"""
root_cause_agent.py — Master Root Cause Intelligence Agent.

Determines the most probable chain of causes behind an incident through a 7-phase reasoning pipeline.
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.types import Capability
from app.modules.agents.root_cause.causal_graph import CausalGraphBuilder
from app.modules.agents.root_cause.collector import EvidenceCollector
from app.modules.agents.root_cause.confidence import RootCauseConfidenceEngine
from app.modules.agents.root_cause.events import RootCauseEventGenerator
from app.modules.agents.root_cause.explanation import RootCauseExplanationGenerator
from app.modules.agents.root_cause.hypotheses import HypothesisGenerator
from app.modules.agents.root_cause.models import RootCauseAgentResult
from app.modules.agents.root_cause.ranking import HypothesisRanker
from app.modules.agents.root_cause.recommendations import CorrectiveRecommendationEngine
from app.modules.agents.root_cause.scorer import HypothesisScorer
from app.modules.agents.root_cause.timeline import TimelineReconstructor

log = get_logger("agents.root_cause.orchestrator")


class RootCauseAgent(BaseAgent):
    """
    Master Root Cause Intelligence Agent.

    Orchestrates 7 Reasoning Phases:
      Phase 1: Multi-Source Evidence Collection
      Phase 2: Chronological Timeline Reconstruction
      Phase 3: Causal Graph Building
      Phase 4: Multi-Hypothesis Generation
      Phase 5: Weighted Multi-Factor Evidence Scoring
      Phase 6: Hypothesis Ranking
      Phase 7: Grounded XAI Explanation & Categorized Action Recommendations.
    """

    name: str = "RootCauseAgent"
    version: str = "1.0.0"
    description: str = "Reconstructs causal failure chains and discovers root causes."
    capabilities: list[Capability] = [Capability.ROOT_CAUSE, Capability.GRAPH_SEARCH]

    async def can_handle(self, context: AgentContext) -> bool:
        return "incident" in context.query.lower() or "cause" in context.query.lower() or "why" in context.query.lower()

    async def _run(self, context: AgentContext) -> AgentResult:
        incident_id = context.target_entity_id or "INC-01"
        log.info(f"Running 7-phase Root Cause Analysis for incident '{incident_id}'")

        # Phase 1: Evidence Collection
        evidence_bundle = EvidenceCollector.collect_evidence(context)

        # Phase 2: Timeline Reconstruction
        timeline = TimelineReconstructor.reconstruct_timeline(evidence_bundle)

        # Phase 3: Causal Graph Building
        causal_graph = CausalGraphBuilder.build_causal_graph(evidence_bundle, timeline)

        # Phase 4: Hypothesis Generation
        hypotheses = HypothesisGenerator.generate_hypotheses(evidence_bundle, causal_graph)

        # Phase 5: Multi-Factor Evidence Scoring
        scored_hypotheses = HypothesisScorer.score_hypotheses(hypotheses, evidence_bundle)

        # Phase 6: Hypothesis Ranking
        ranked_hypotheses = HypothesisRanker.rank_hypotheses(scored_hypotheses)

        primary_h = ranked_hypotheses[0]

        # Phase 7: Explanation & Recommendations
        explanation = RootCauseExplanationGenerator.generate_explanation(primary_h, evidence_bundle)
        flat_recs, categorized_recs = CorrectiveRecommendationEngine.generate_recommendations(primary_h)

        confidence = RootCauseConfidenceEngine.compute_confidence(ranked_hypotheses, evidence_bundle)

        # Domain Events
        events = RootCauseEventGenerator.generate_events(
            agent_name=self.name,
            incident_id=incident_id,
            primary_hypothesis=primary_h,
            actions=flat_recs,
            trace_id=context.trace_id,
        )

        evidence_items = [
            f"Evaluated {len(ranked_hypotheses)} hypotheses across {len(timeline)} timeline events",
            f"Primary root cause identified: {primary_h.root_cause_candidate}",
        ]
        evidence_items.extend(primary_h.supporting_evidence)

        return RootCauseAgentResult(
            agent_name=self.name,
            success=True,
            confidence=confidence,
            evidence=evidence_items,
            recommendations=flat_recs,
            events=events,
            incident_id=incident_id,
            timeline=timeline,
            causal_graph=causal_graph,
            ranked_hypotheses=ranked_hypotheses,
            primary_root_cause=primary_h.root_cause_candidate,
            corrective_actions=categorized_recs,
            output_data={
                "incident_id": incident_id,
                "primary_root_cause": primary_h.root_cause_candidate,
                "confidence": confidence,
                "hypotheses_count": len(ranked_hypotheses),
                "corrective_actions": categorized_recs,
            },
            explanation=explanation,
        )
