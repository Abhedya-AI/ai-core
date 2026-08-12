"""
test_ppe_engine.py — PPE Compliance Engine Unit Tests.
"""
import pytest
from app.modules.vision.intelligence.ppe_engine import PPEComplianceEngine


def test_ppe_evaluation_full_compliance():
    engine = PPEComplianceEngine()
    score, missing, viol = engine.evaluate(
        detected_ppe=["HELMET", "SAFETY_VEST"],
        camera_id="CAM-01",
        zone_id="ZONE-A",
    )
    assert score == 100.0
    assert len(missing) == 0
    assert viol is None


def test_ppe_evaluation_violation():
    engine = PPEComplianceEngine()
    score, missing, viol = engine.evaluate(
        detected_ppe=["SAFETY_VEST"],
        camera_id="CAM-01",
        zone_id="ZONE-A",
        worker_id="worker-01",
    )
    assert score == 50.0
    assert "HELMET" in missing
    assert viol is not None
    assert viol.compliance_score == 50.0
