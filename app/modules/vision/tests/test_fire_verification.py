"""
test_fire_verification.py — Multi-Modal Fire Verification Unit Tests.
"""
import pytest
from app.modules.vision.intelligence.fire_smoke_verification import FireSmokeVerificationEngine
from app.modules.vision.domain.enums.vision_safety_enums import VerificationStatus


def test_fire_multi_modal_confirmation():
    engine = FireSmokeVerificationEngine()
    status, f_conf, viol, emerg = engine.verify_fire_smoke(
        camera_id="CAM-01",
        zone_id="ZONE-A",
        visual_type="FIRE",
        camera_confidence=0.9,
        sensor_smoke_detected=True,
        sensor_temp_celsius=65.0,
    )
    assert status == VerificationStatus.CONFIRMED
    assert f_conf >= 0.8
    assert viol is not None
    assert emerg is not None
    assert emerg.emergency_type == "CONFIRMED_FIRE"
