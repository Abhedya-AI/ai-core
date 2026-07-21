import pytest

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.vision import (
    ConfidenceEngine,
    DetectionFusionEngine,
    EntityTracker,
    FireModule,
    ObjectDetector,
    OccupancyModule,
    OCRModule,
    PPEModule,
    SmokeModule,
    SpillModule,
    VisionAgent,
    VisionAgentResult,
)


def test_object_detector_and_tracker():
    """Verify ObjectDetector inference and EntityTracker track ID assignment."""
    detector = ObjectDetector()
    tracker = EntityTracker()

    detections = detector.detect_objects(frame_data=["person", "helmet"], camera_id="CAM-01")
    assert len(detections) == 2

    tracked = tracker.track_entities("CAM-01", detections)
    assert tracked[0].track_id is not None
    assert "TRACK-PERSON" in tracked[0].track_id


def test_ppe_and_safety_modules():
    """Verify PPE compliance, Smoke vs Fire separation, and Spill detection."""
    detector = ObjectDetector()
    detections = detector.detect_objects(frame_data=["person", "smoke", "oil_spill"])

    # PPE Evaluation (Person present, helmet missing)
    ppe_violations = PPEModule.evaluate_compliance(detections)
    assert len(ppe_violations) >= 1
    assert "Missing Helmet" in ppe_violations[0]

    # Smoke vs Fire Separation
    smoke_det = SmokeModule.detect_smoke(detections)
    fire_det = FireModule.detect_fire(detections)
    assert len(smoke_det) == 1
    assert len(fire_det) == 0

    # Spill Detection
    spills = SpillModule.detect_spills(detections)
    assert len(spills) == 1
    assert spills[0].label == "oil_spill"


def test_occupancy_and_ocr_modules():
    """Verify occupancy headcount evaluation and OCR tag extraction."""
    detector = ObjectDetector()
    detections = detector.detect_objects(frame_data=["person"] * 15)

    occupancy = OccupancyModule.evaluate_occupancy("ZONE-A", detections, max_capacity=12)
    assert occupancy["headcount"] == 15
    assert occupancy["status"] == "OVER_CAPACITY"

    ocr_tags = OCRModule.extract_ocr_tags(detections, frame_metadata={"ocr_text": ["TANK-T12"]})
    assert "TANK-T12" in ocr_tags


def test_detection_fusion_and_confidence_engine():
    """Verify DetectionFusionEngine and ConfidenceEngine operational metrics."""
    detector = ObjectDetector()
    detections = detector.detect_objects(frame_data=["person", "smoke"])

    fusion_score = DetectionFusionEngine.fuse_multi_camera({"CAM-01": detections, "CAM-02": detections})
    assert fusion_score >= 0.9

    confidence = ConfidenceEngine.compute_confidence(detections, fusion_score)
    assert confidence.operational_confidence >= 0.85


@pytest.mark.asyncio
async def test_vision_agent_end_to_end_execution():
    """Verify VisionAgent end-to-end execution workflow returning VisionAgentResult."""
    agent = VisionAgent()
    ctx = AgentContext(
        query="Analyze CCTV feed from CAM-01 in Zone B",
        zone_id="ZONE-B",
        metadata={
            "camera_id": "CAM-01",
            "detections": ["person", "smoke", "fire"],
        },
    )

    result = await agent.execute(ctx)
    assert isinstance(result, VisionAgentResult)
    assert result.success is True
    assert result.confidence > 0.8
    assert len(result.events) >= 2  # SmokeDetected/FireDetected + VisualObservationRecorded
    event_types = [e.event_type for e in result.events]
    assert "FireDetected" in event_types
    assert "SmokeDetected" in event_types
