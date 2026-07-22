import pytest

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.root_cause import (
    CausalGraphBuilder,
    EvidenceCollector,
    HypothesisGenerator,
    HypothesisRanker,
    HypothesisScorer,
    RootCauseAgent,
    RootCauseAgentResult,
    TimelineReconstructor,
)


def test_evidence_collection_and_timeline_reconstruction():
    """Verify Phase 1 Evidence Collection and Phase 2 Timeline Reconstruction."""
    ctx = AgentContext(
        query="Investigate explosion incident INC-01",
        target_entity_id="INC-01",
        sensor_data=[{"id": "S-01", "value": 180, "threshold": 100, "timestamp": "08:14"}],
        vision_events=[{"camera_id": "CAM-01", "detection": "GAS_PLUME", "timestamp": "08:20"}],
        metadata={"maintenance_logs": [{"asset": "VALVE-V12", "overdue_days": 34}]},
    )

    bundle = EvidenceCollector.collect_evidence(ctx)
    assert bundle.incident_id == "INC-01"
    assert len(bundle.sensor_timeline) == 1

    timeline = TimelineReconstructor.reconstruct_timeline(bundle)
    assert len(timeline) >= 3
    assert timeline[0].source in ("MAINTENANCE", "SENSOR", "VISION")


def test_causal_graph_hypotheses_and_ranking():
    """Verify Phase 3 Causal Graph, Phase 4 Hypotheses, Phase 5 Scoring, and Phase 6 Ranking."""
    ctx = AgentContext(query="Incident INC-01", target_entity_id="INC-01")
    bundle = EvidenceCollector.collect_evidence(ctx)
    timeline = TimelineReconstructor.reconstruct_timeline(bundle)

    causal_edges = CausalGraphBuilder.build_causal_graph(bundle, timeline)
    assert len(causal_edges) == 3

    hypotheses = HypothesisGenerator.generate_hypotheses(bundle, causal_edges)
    assert len(hypotheses) == 3

    scored = HypothesisScorer.score_hypotheses(hypotheses, bundle)
    ranked = HypothesisRanker.rank_hypotheses(scored)

    assert ranked[0].rank == 1
    assert ranked[0].hypothesis_id == "HYP-A"
    assert ranked[0].confidence_score >= 0.90


@pytest.mark.asyncio
async def test_root_cause_agent_end_to_end_execution():
    """Verify RootCauseAgent 7-phase end-to-end execution returning RootCauseAgentResult."""
    agent = RootCauseAgent()
    ctx = AgentContext(
        query="Why did explosion incident INC-01 happen?",
        target_entity_id="INC-01",
        sensor_data=[{"id": "S-01", "value": 180, "threshold": 100}],
        metadata={"maintenance_logs": [{"asset": "VALVE-V12", "overdue_days": 34}]},
    )

    result = await agent.execute(ctx)
    assert isinstance(result, RootCauseAgentResult)
    assert result.success is True
    assert result.primary_root_cause == "VALVE-V12-FAILURE"
    assert len(result.ranked_hypotheses) == 3
    assert len(result.events) == 3
    event_types = [e.event_type for e in result.events]
    assert "RootCauseIdentified" in event_types
    assert "CorrectiveActionRecommended" in event_types
    assert "InvestigationCompleted" in event_types
    assert "Immediate" in result.corrective_actions
