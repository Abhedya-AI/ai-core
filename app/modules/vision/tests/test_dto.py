"""
tests/test_dto.py — Unit tests for application DTOs.
"""

import pytest
from app.modules.vision.application.dto.analyze_response import FrameAnalysisResult
from app.modules.vision.domain.value_objects import RiskScore
from app.modules.vision.domain.enums import RiskLevel, HazardType
from app.modules.vision.domain.entities import Hazard, VisionEvent

def test_frame_analysis_result_default_properties():
    result = FrameAnalysisResult(
        frame_id="frame-123",
        camera_id="cam-456",
        processing_time_ms=12.5,
        model_version="yolov8n-test"
    )
    assert result.frame_id == "frame-123"
    assert result.camera_id == "cam-456"
    assert result.processing_time_ms == 12.5
    assert result.model_version == "yolov8n-test"
    assert result.detection_count == 0
    assert result.hazard_count == 0
    assert result.is_critical is False
    assert "cam-456" in result.summary()
    assert "12.5ms" in result.summary()

def test_frame_analysis_result_is_critical_from_score():
    score_low = RiskScore(score=0.1, level=RiskLevel.LOW, reason="low")
    result_low = FrameAnalysisResult(
        frame_id="f1", camera_id="c1", processing_time_ms=10.0,
        risk_score=score_low
    )
    assert result_low.is_critical is False

    score_crit = RiskScore(score=0.8, level=RiskLevel.CRITICAL, reason="critical")
    result_crit = FrameAnalysisResult(
        frame_id="f1", camera_id="c1", processing_time_ms=10.0,
        risk_score=score_crit
    )
    assert result_crit.is_critical is True

def test_frame_analysis_result_is_critical_from_event():
    # When event is present, it should take precedence for is_critical check
    score_low = RiskScore(score=0.1, level=RiskLevel.LOW, reason="low")
    score_crit = RiskScore(score=0.8, level=RiskLevel.CRITICAL, reason="critical")
    
    event = VisionEvent(
        camera_id="c1",
        frame_id="f1",
        detections=[],
        hazards=[],
        risk_score=score_crit
    )
    
    result = FrameAnalysisResult(
        frame_id="f1", camera_id="c1", processing_time_ms=10.0,
        risk_score=score_low,
        event=event
    )
    assert result.is_critical is True
