"""
test_temporal_reasoning.py — Temporal Reasoning Engine Unit Tests.
"""
import pytest
from app.modules.vision.intelligence.temporal_reasoning_engine import TemporalReasoningEngine


def test_temporal_reasoning_persistence():
    engine = TemporalReasoningEngine(min_persistence_frames=3, window_seconds=60.0)
    key = "worker-101:UNSAFE_BEHAVIOR"

    # Frame 1
    is_persistent, count, avg_conf = engine.evaluate_temporal_pattern(key, "UNSAFE_BEHAVIOR", 0.9, 100.0)
    assert is_persistent is False
    assert count == 1

    # Frame 2
    is_persistent, count, avg_conf = engine.evaluate_temporal_pattern(key, "UNSAFE_BEHAVIOR", 0.95, 101.0)
    assert is_persistent is False
    assert count == 2

    # Frame 3 — Confirmed!
    is_persistent, count, avg_conf = engine.evaluate_temporal_pattern(key, "UNSAFE_BEHAVIOR", 0.92, 102.0)
    assert is_persistent is True
    assert count == 3
    assert avg_conf == 0.92
