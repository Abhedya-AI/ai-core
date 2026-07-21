import pytest

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.risk import (
    PriorityEnum,
    RiskAgent,
    RiskAgentResult,
    RiskAnalyzer,
    RiskEvidence,
    RiskExplanationGenerator,
    RiskPropagationEngine,
    RiskRecommendationEngine,
    RiskScorer,
    SeverityEnum,
    evaluate_risk_policy,
)


def test_deterministic_risk_scorer():
    """Verify deterministic risk scoring logic."""
    evidence = RiskEvidence(
        sensor_readings=[{"value": 150, "threshold": 100}],
        maintenance_logs=[{"overdue": True}],
        vision_events=[{"event": "SMOKE_DETECTED"}],
    )
    score = RiskScorer.compute_score(evidence, target_id="TANK-T12")
    assert score.score_value >= 70.0
    assert score.severity == SeverityEnum.HIGH
    assert score.priority == PriorityEnum.P2


def test_risk_policy_evaluation():
    """Verify risk policy rules and emergency triggers."""
    evidence = RiskEvidence(
        sensor_readings=[{"value": 200, "threshold": 100}],
        maintenance_logs=[{"overdue": True}],
        vision_events=[{"event": "FIRE"}],
    )
    score = RiskScorer.compute_score(evidence)
    policy = evaluate_risk_policy(score, hazard_type="gas leak near Tank T-12")

    assert policy["trigger_emergency"] is True
    assert policy["requires_evacuation"] is True
    assert policy["event_type"] == "HighRiskDetected"


def test_risk_recommendation_categorization():
    """Verify recommendations are prioritized and categorized by urgency."""
    evidence = RiskEvidence(sensor_readings=[{"value": 200, "threshold": 100}])
    score = RiskScorer.compute_score(evidence)

    flattened, categorized = RiskRecommendationEngine.generate_recommendations("TANK-T12", score, ["TANK-T12", "ZONE-B"])
    assert "Immediate" in categorized
    assert "Within 30 Minutes" in categorized
    assert "Within 24 Hours" in categorized
    assert len(flattened) > 0


@pytest.mark.asyncio
async def test_risk_agent_end_to_end_execution():
    """Verify RiskAgent end-to-end execution workflow returning RiskAgentResult."""
    agent = RiskAgent()
    ctx = AgentContext(
        query="Methane gas leak near Tank T-12",
        target_entity_id="TANK-T12",
        zone_id="ZONE-B",
        sensor_data=[{"value": 180, "threshold": 100}, {"value": 220, "threshold": 100}],
        vision_events=[{"event": "GAS_LEAK_VISUAL"}],
        graph_snapshot={"TANK-T12": ["PIPE-1", "ZONE-B"]},
    )

    result = await agent.execute(ctx)
    assert isinstance(result, RiskAgentResult)
    assert result.success is True
    assert result.risk_score.score_value > 50.0
    assert len(result.events) >= 2  # RiskDetected/HighRiskDetected + EmergencyTriggerRequested
    event_types = [e.event_type for e in result.events]
    assert "EmergencyTriggerRequested" in event_types
    assert "Immediate" in result.categorized_recommendations
