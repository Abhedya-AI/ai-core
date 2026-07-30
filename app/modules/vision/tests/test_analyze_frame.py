"""
tests/test_analyze_frame.py — Unit tests for AnalyzeFrameUseCase.

AnalyzeFrameUseCase is responsible for:
  • Calling the FrameDetector.
  • Mapping detections.
  • Returning a FrameAnalysisResult.
"""

import pytest
from app.modules.vision.application.use_cases.analyze_frame import AnalyzeFrameUseCase, FrameDetector
from app.modules.vision.domain.entities import Detection
from app.modules.vision.domain.enums import HazardType
from app.modules.vision.domain.value_objects import BoundingBox
from app.modules.vision.infrastructure.detector import StubDetector
from app.modules.vision.schemas.request import AnalyzeFrameRequest
from app.modules.vision.application.exceptions import FrameReadError, DetectorUnavailableError

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

@pytest.mark.asyncio
async def test_analyze_frame_empty_image_raises_error():
    use_case = AnalyzeFrameUseCase(detector=StubDetector())
    with pytest.raises(FrameReadError):
        await use_case.execute(b"", _make_request())

@pytest.mark.asyncio
async def test_analyze_frame_stub_detector_success():
    use_case = AnalyzeFrameUseCase(detector=StubDetector())
    result = await use_case.execute(b"fake-image", _make_request())
    
    assert result.detection_count == 0
    assert result.model_version == "stub-detector-v0"
    assert result.processing_time_ms >= 0.0

@pytest.mark.asyncio
async def test_analyze_frame_fire_detector_success():
    use_case = AnalyzeFrameUseCase(detector=FireDetector())
    result = await use_case.execute(b"fake-image", _make_request())
    
    assert result.detection_count == 1
    assert result.model_version == "yolov8n-fire-test"
    assert result.detections[0].hazard_type == HazardType.FIRE
    assert result.detections[0].confidence == 0.95

@pytest.mark.asyncio
async def test_analyze_frame_detector_failure_raises_unavailable():
    class FailingDetector(FrameDetector):
        async def detect(self, image_bytes, frame_id, camera_id, min_confidence=0.4):
            raise ValueError("GPU out of memory")
            
    use_case = AnalyzeFrameUseCase(detector=FailingDetector())
    with pytest.raises(DetectorUnavailableError):
        await use_case.execute(b"fake-image", _make_request())
