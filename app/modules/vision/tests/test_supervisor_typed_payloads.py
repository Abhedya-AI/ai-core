"""
test_supervisor_typed_payloads.py — Strongly Typed Supervisor Payload Tests.
"""
import pytest
from app.modules.vision.domain.entities.vision_assessment import (
    VisionAssessment, VisionEmergencyCandidate, VisionIncidentCandidate, VisionRecommendation
)
from app.modules.vision.domain.entities.vision_evidence import VisionEvidence


def test_supervisor_typed_contract_serialization():
    ev = VisionEvidence(
        camera_id="CAM-01",
        zone_id="ZONE-A",
        primary_detection_label="Worker",
        detection_confidence=0.9,
        reasoning_summary="Summary",
    )
    rec = VisionRecommendation(
        title="Dispatch Inspection",
        description="Inspect Zone A",
        priority="HIGH",
    )
    inc = VisionIncidentCandidate(
        title="Near Miss Equipment Interaction",
        severity="HIGH",
        zone_id="ZONE-A",
        camera_id="CAM-01",
        hazard_type="PROXIMITY",
        summary="Worker near forklift",
    )
    emerg = VisionEmergencyCandidate(
        emergency_type="FALL_MEDICAL_EMERGENCY",
        zone_id="ZONE-A",
        severity="CRITICAL",
        trigger_reason="Worker fall detected",
    )

    assessment = VisionAssessment(
        camera_id="CAM-01",
        zone_id="ZONE-A",
        assessment_type="FALL",
        overall_risk_score=95.0,
        risk_level="CRITICAL",
        evidence=ev,
        recommendations=[rec],
        incident_candidate=inc,
        emergency_candidate=emerg,
    )

    d = assessment.model_dump()
    assert d["camera_id"] == "CAM-01"
    assert d["emergency_candidate"]["emergency_type"] == "FALL_MEDICAL_EMERGENCY"
    assert d["recommendations"][0]["priority"] == "HIGH"
