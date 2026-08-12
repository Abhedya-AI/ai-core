"""
test_recommendation_explainability.py — Recommendation & Explainability Engine Unit Tests.
"""
import pytest
from app.modules.vision.intelligence.policy_mapper import PolicyMapper
from app.modules.vision.intelligence.action_generator import ActionGenerator
from app.modules.vision.intelligence.recommendation_service import RecommendationService
from app.modules.vision.intelligence.explainability_engine import ExplainabilityEngine
from app.modules.vision.domain.entities.vision_evidence import VisionEvidence


def test_policy_mapper():
    policies = PolicyMapper.map_policies("PPE")
    assert len(policies) > 0
    assert "OSHA" in policies[0]["code"]


def test_action_generator():
    recs = ActionGenerator.generate_actions("PPE", "HIGH", "ZONE-A", worker_id="w-1")
    assert len(recs) > 0
    assert recs[0].action_type in ("HALT_WORK_DISPATCH", "SUPPLY_PPE")


def test_recommendation_service():
    service = RecommendationService()
    recs = service.generate_recommendations("PPE", "HIGH", "ZONE-A", worker_id="w-1")
    assert len(recs) > 0
    assert recs[0].policy_reference is not None


def test_rich_explainability_engine():
    engine = ExplainabilityEngine()
    ev = VisionEvidence(
        camera_id="CAM-01",
        zone_id="ZONE-A",
        primary_detection_label="Worker",
        detection_confidence=0.95,
        reasoning_summary="Missing helmet detected",
    )
    explanation = engine.build_explanation(
        assessment_id="ass-100",
        main_reason="Missing helmet detected",
        confidence=0.95,
        evidence=ev,
        recommendations=[],
    )
    assert explanation.explanation_id == "expl-ass-100"
    assert explanation.confidence_score == 0.95
    assert len(explanation.alternative_interpretations) > 0
