"""
tests/test_process_detection.py — End-to-end orchestration unit/integration tests.

Tests the full ProcessDetectionUseCase pipeline using in-memory stubs:
  • StubDetector / FireDetector
  • InMemoryVisionRepository
  • RiskEngine
  • Mocked Kafka publishing
"""

import pytest
from app.modules.vision.application.use_cases.process_detection import ProcessDetectionUseCase
from app.modules.vision.application.use_cases.analyze_frame import FrameDetector
from app.modules.vision.domain.entities import Detection, VisionEvent
from app.modules.vision.domain.enums import DetectionStatus, HazardType, RiskLevel
from app.modules.vision.domain.repositories import VisionRepository
from app.modules.vision.domain.value_objects import BoundingBox
from app.modules.vision.infrastructure.detector import StubDetector
from app.modules.vision.schemas.request import AnalyzeFrameRequest

# ── Fakes ─────────────────────────────────────────────────────────────────────

class InMemoryVisionRepository(VisionRepository):
    """Simple in-memory repository for testing — no DB needed."""

    def __init__(self):
        self._events: dict[str, VisionEvent] = {}
        self._detections: dict[str, list[Detection]] = {}

    async def save_event(self, event: VisionEvent) -> VisionEvent:
        self._events[event.event_id] = event
        self._detections[event.event_id] = event.detections
        return event

    async def get_event(self, event_id: str) -> VisionEvent | None:
        return self._events.get(event_id)

    async def list_events(self, **kwargs) -> list[VisionEvent]:
        return list(self._events.values())

    async def save_detection(self, detection: Detection) -> Detection:
        return detection

    async def list_detections_for_event(self, event_id: str) -> list[Detection]:
        return self._detections.get(event_id, [])


class FireDetector(FrameDetector):
    """Fake detector that always returns a FIRE detection."""
    model_version = "yolov8n-fire-test"

    async def detect(self, image_bytes, frame_id, camera_id, min_confidence=0.4):
        return [
            Detection(
                hazard_type=HazardType.FIRE,
                confidence=0.95,
                bounding_box=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.5, y_max=0.5),
                frame_id=frame_id,
                camera_id=camera_id,
            )
        ]


def _make_request(camera_id="CAM-01", frame_id="frame-001") -> AnalyzeFrameRequest:
    return AnalyzeFrameRequest(camera_id=camera_id, frame_id=frame_id)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestProcessDetectionUseCase:

    @pytest.mark.asyncio
    async def test_stub_detector_returns_zero_risk(self):
        use_case = ProcessDetectionUseCase(
            detector=StubDetector(),
            repository=InMemoryVisionRepository(),
        )
        result = await use_case.execute(b"fake-image", _make_request())

        assert result.detection_count == 0
        assert result.hazard_count == 0
        assert result.risk_score.level == RiskLevel.LOW
        assert result.risk_score.score == 0.0
        assert result.event is not None
        assert result.event.risk_score.score == 0.0

    @pytest.mark.asyncio
    async def test_fire_detector_triggers_critical(self):
        use_case = ProcessDetectionUseCase(
            detector=FireDetector(),
            repository=InMemoryVisionRepository(),
        )
        result = await use_case.execute(b"fake-image", _make_request())

        assert result.detection_count == 1
        assert result.hazard_count == 1
        assert result.risk_score.level == RiskLevel.CRITICAL
        assert result.is_critical is True
        assert result.hazards[0].hazard_type == HazardType.FIRE

    @pytest.mark.asyncio
    async def test_risk_score_has_reason(self):
        use_case = ProcessDetectionUseCase(
            detector=FireDetector(),
            repository=InMemoryVisionRepository(),
        )
        result = await use_case.execute(b"fake-image", _make_request())
        assert result.risk_score.reason != ""
        assert "FIRE" in result.risk_score.reason

    @pytest.mark.asyncio
    async def test_detection_default_status_pending(self):
        use_case = ProcessDetectionUseCase(
            detector=FireDetector(),
            repository=InMemoryVisionRepository(),
        )
        result = await use_case.execute(b"fake-image", _make_request())
        assert result.detections[0].status == DetectionStatus.PENDING

    @pytest.mark.asyncio
    async def test_event_persisted_in_repo(self):
        repo = InMemoryVisionRepository()
        use_case = ProcessDetectionUseCase(
            detector=StubDetector(),
            repository=repo,
        )
        result = await use_case.execute(b"fake-image", _make_request())
        retrieved = await repo.get_event(result.event.event_id)

        assert retrieved is not None
        assert retrieved.event_id == result.event.event_id

    @pytest.mark.asyncio
    async def test_frame_id_auto_generated_if_missing(self):
        request = AnalyzeFrameRequest(camera_id="CAM-01", frame_id=None)
        use_case = ProcessDetectionUseCase(
            detector=StubDetector(),
            repository=InMemoryVisionRepository(),
        )
        result = await use_case.execute(b"fake-image", request)
        assert result.frame_id != ""
        assert len(result.frame_id) == 36  # UUID length

    @pytest.mark.asyncio
    async def test_camera_id_propagated(self):
        use_case = ProcessDetectionUseCase(
            detector=StubDetector(),
            repository=InMemoryVisionRepository(),
        )
        result = await use_case.execute(
            b"fake-image",
            _make_request(camera_id="SPECIAL-CAM-99"),
        )
        assert result.camera_id == "SPECIAL-CAM-99"

    @pytest.mark.asyncio
    async def test_actionable_hazards_empty_for_low_risk(self):
        use_case = ProcessDetectionUseCase(
            detector=StubDetector(),
            repository=InMemoryVisionRepository(),
        )
        result = await use_case.execute(b"fake-image", _make_request())
        assert result.event.actionable_hazards == []

    @pytest.mark.asyncio
    async def test_bounding_box_field_names(self):
        """BoundingBox in detections must expose x_min/y_min/x_max/y_max."""
        use_case = ProcessDetectionUseCase(
            detector=FireDetector(),
            repository=InMemoryVisionRepository(),
        )
        result = await use_case.execute(b"fake-image", _make_request())
        bb = result.detections[0].bounding_box
        assert hasattr(bb, "x_min")
        assert hasattr(bb, "x_max")
        assert not hasattr(bb, "x1")
