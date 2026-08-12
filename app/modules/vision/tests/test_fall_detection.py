"""
test_fall_detection.py — Fall Detection Engine Unit Tests.
"""
import pytest
from app.modules.vision.intelligence.fall_detection_engine import FallDetectionEngine


def test_fall_detection_confirmation():
    engine = FallDetectionEngine(confirmation_frames_required=2)

    # Frame 1
    is_fall, viol, emerg = engine.evaluate_pose_and_motion("w-1", "CAM-01", "ZONE-A", 1.5, 2.0)
    assert is_fall is False

    # Frame 2 — Confirmed
    is_fall, viol, emerg = engine.evaluate_pose_and_motion("w-1", "CAM-01", "ZONE-A", 1.5, 2.0)
    assert is_fall is True
    assert viol is not None
    assert emerg is not None
    assert emerg.emergency_type == "FALL_MEDICAL_EMERGENCY"
