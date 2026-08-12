"""
test_unsafe_behavior_engine.py — Unsafe Behavior Engine Unit Tests.
"""
import pytest
from app.modules.vision.intelligence.unsafe_behavior_engine import UnsafeBehaviorEngine
from app.modules.vision.domain.enums.vision_safety_enums import UnsafeBehaviorType


def test_running_in_hazardous_zone():
    engine = UnsafeBehaviorEngine()
    viol = engine.evaluate_behavior(
        camera_id="CAM-01",
        zone_id="ZONE-A",
        behavior_type=UnsafeBehaviorType.RUNNING_IN_HAZARDOUS_ZONE,
        velocity=3.2,
    )
    assert viol is not None
    assert viol.severity == "HIGH"
    assert "running" in viol.description.lower()


def test_suspended_load_threat():
    engine = UnsafeBehaviorEngine()
    viol = engine.evaluate_behavior(
        camera_id="CAM-01",
        zone_id="ZONE-A",
        behavior_type=UnsafeBehaviorType.STANDING_UNDER_SUSPENDED_LOAD,
        is_suspended_load_above=True,
    )
    assert viol is not None
    assert viol.severity == "CRITICAL"
