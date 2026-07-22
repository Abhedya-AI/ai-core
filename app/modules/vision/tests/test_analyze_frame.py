"""
tests/test_analyze_frame.py — Integration-style tests for AnalyzeFrameUseCase.

These tests exercise the full pipeline with:
  • An in-memory stub repository (no DB required)
  • The StubDetector (no model required)
  • A real RiskEngine

All async because the use-case is async.
"""

import pytest
import pytest_asyncio

from app.modules.vision.application.analyze_frame import AnalyzeFrameUseCase, FrameDetector
from app.modules.vision.application.calculate_risk import RiskEngine
from app.modules.vision.domain.entities import Detection, VisionEvent
from app.modules.vision.domain.enums import HazardType, RiskLevel
from app.modules.vision.domain.repository import VisionRepository
from app.modules.vision.domain.value_objects import BoundingBox, RiskScore
from app.modules.vision.infrastructure.detector import StubDetector
from app.modules.vision.schemas.request import AnalyzeFrameRequest


# ── Fakes ─────────────────────────────────────────────────────────────────────

class InMemoryVisionRepository(VisionRepository):
    """Simple in-memory repository for testing — no DB needed."""

    def __init__(self):
        self._events: dict[str, VisionEvent] = {}

    async def save_event(self, event: VisionEvent) -> VisionEvent:
        self._events[event.event_id] = event
        return event

    async def get_event(self, event_id: str) -> VisionEvent | None:
        return self._events.get(event_id)

    async def list_events(self, **kwargs) -> list[VisionEvent]:
        return list(self._events.values())

    async def save_detection(self, detection: Detection) -> Detection:
        return detection

    async def list_detections_for_event(self, event_id: str) -> list[Detection]:
        event = self._events.get(event_id)
        return event.detections if event else []


class FireDetector(FrameDetector):
    """Fake detector that always returns a FIRE detection."""

    async def detect(self, image_bytes, frame_id, camera_id, min_confidence=0.4):
        return [
            Detection(
                hazard_type=HazardType.FIRE,
                confidence=0.95,
                bounding_box=BoundingBox(x1=0.1, y1=0.1, x2=0.5, y2=0.5),
                frame_id=frame_id,
                camera_id=camera_id,
            )
        ]


def _make_request(camera_id="CAM-01", frame_id="frame-001") -> AnalyzeFrameRequest:
    return AnalyzeFrameRequest(camera_id=camera_id, frame_id=frame_id)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAnalyzeFrameUseCase:

    @pytest.mark.asyncio
    async def test_stub_detector_returns_zero_risk(self):
        use_case = AnalyzeFrameUseCase(
            detector=StubDetector(),
            repository=InMemoryVisionRepository(),
        )
        event = await use_case.execute(b"fake-image", _make_request())

        assert event.detection_count == 0
        assert event.hazard_count == 0
        assert event.risk_score.level == RiskLevel.LOW
        assert event.risk_score.value == 0.0

    @pytest.mark.asyncio
    async def test_fire_detector_triggers_critical(self):
        use_case = AnalyzeFrameUseCase(
            detector=FireDetector(),
            repository=InMemoryVisionRepository(),
        )
        event = await use_case.execute(b"fake-image", _make_request())

        assert event.detection_count == 1
        assert event.hazard_count == 1
        assert event.risk_score.level == RiskLevel.CRITICAL
        assert event.is_critical is True
        assert event.hazards[0].hazard_type == HazardType.FIRE

    @pytest.mark.asyncio
    async def test_event_persisted_in_repo(self):
        repo = InMemoryVisionRepository()
        use_case = AnalyzeFrameUseCase(
            detector=StubDetector(),
            repository=repo,
        )
        event = await use_case.execute(b"fake-image", _make_request())
        retrieved = await repo.get_event(event.event_id)

        assert retrieved is not None
        assert retrieved.event_id == event.event_id

    @pytest.mark.asyncio
    async def test_frame_id_auto_generated_if_missing(self):
        request = AnalyzeFrameRequest(camera_id="CAM-01", frame_id=None)
        use_case = AnalyzeFrameUseCase(
            detector=StubDetector(),
            repository=InMemoryVisionRepository(),
        )
        event = await use_case.execute(b"fake-image", request)
        assert event.frame_id != ""
        assert len(event.frame_id) == 36  # UUID length

    @pytest.mark.asyncio
    async def test_camera_id_propagated(self):
        use_case = AnalyzeFrameUseCase(
            detector=StubDetector(),
            repository=InMemoryVisionRepository(),
        )
        event = await use_case.execute(
            b"fake-image",
            _make_request(camera_id="SPECIAL-CAM-99"),
        )
        assert event.camera_id == "SPECIAL-CAM-99"

    @pytest.mark.asyncio
    async def test_actionable_hazards_empty_for_low_risk(self):
        use_case = AnalyzeFrameUseCase(
            detector=StubDetector(),
            repository=InMemoryVisionRepository(),
        )
        event = await use_case.execute(b"fake-image", _make_request())
        assert event.actionable_hazards == []
