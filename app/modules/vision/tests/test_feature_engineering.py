"""
test_feature_engineering.py — Feature Engineering Unit Tests.
"""
import pytest
from app.modules.vision.application.feature_engineering import VisionFeatureEngine, VisionFeatureVector


def test_velocity_and_trajectory_calculation():
    engine = VisionFeatureEngine()
    positions = [
        (10.0, 10.0, 100.0),
        (20.0, 10.0, 101.0),  # moved dx=10px in dt=1sec -> 10px * 0.05 = 0.5 m/s
    ]
    velocity, trajectory = engine.compute_velocity_and_trajectory(positions, pixel_to_meter_ratio=0.05)
    assert velocity == 0.5
    assert trajectory == (1.0, 0.0)


def test_ppe_score_calculation():
    engine = VisionFeatureEngine()
    score = engine.compute_ppe_score(["HELMET", "SAFETY_VEST"], ["HELMET", "SAFETY_VEST", "GLOVES"])
    assert score == 66.7


def test_detection_stability():
    engine = VisionFeatureEngine()
    st = engine.compute_detection_stability([0.9, 0.92, 0.89, 0.91])
    assert st >= 0.9


def test_crowd_density():
    engine = VisionFeatureEngine()
    density = engine.compute_crowd_density(worker_count=10, zone_area_sqm=100.0)
    assert density == 0.1
