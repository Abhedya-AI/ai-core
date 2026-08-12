"""
application/services/vision_orchestrator.py — VisionOrchestrator service.

What this is
────────────
VisionOrchestrator is a stateful service object that holds the detector
and repository, and exposes a single `analyze()` method.

It is the object that FastAPI's dependency injection provides to routes.

    # In routes.py:
    async def analyze_frame(
        orchestrator: VisionOrchestrator = Depends(get_orchestrator),
        ...
    ):
        result = await orchestrator.analyze(image_bytes, request)

Why separate from ProcessDetectionUseCase?
──────────────────────────────────────────
ProcessDetectionUseCase is stateless and short-lived — it's created fresh
per request with its deps injected by the caller.

VisionOrchestrator is long-lived — it holds the detector reference (which
may be expensive to initialise, e.g. loading a YOLO model into GPU VRAM).
It wraps ProcessDetectionUseCase construction so routes stay clean.

Factory methods
───────────────
  VisionOrchestrator.with_stub(repository)   — test / development
  VisionOrchestrator.with_yolo(repository)   — production (YOLODetector)
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.application.dto.analyze_response import FrameAnalysisResult
from app.modules.vision.application.use_cases.analyze_frame import FrameDetector
from app.modules.vision.application.use_cases.process_detection import (
    ProcessDetectionUseCase,
)
from app.modules.vision.domain.repositories import VisionRepository
from app.modules.vision.schemas.request import AnalyzeFrameRequest

log = get_logger("vision.services.orchestrator")


class VisionOrchestrator:
    """
    Stateful service that wraps ProcessDetectionUseCase.

    Holds the detector reference across requests (avoids re-loading the
    model on every HTTP call).

    Parameters
    ──────────
    detector    A concrete FrameDetector.
    repository  A concrete VisionRepository.
    """

    def __init__(
        self,
        detector:   FrameDetector,
        repository: VisionRepository,
    ) -> None:
        self._detector   = detector
        self._repository = repository

    async def analyze(
        self,
        image_bytes: bytes,
        request:     AnalyzeFrameRequest,
    ) -> FrameAnalysisResult:
        """
        Run the complete detection pipeline and return the result.

        Delegates to ProcessDetectionUseCase. The orchestrator does not
        add logic — it provides a stable, injection-friendly entry point.
        """
        use_case = ProcessDetectionUseCase(
            detector=self._detector,
            repository=self._repository,
        )
        return await use_case.execute(image_bytes, request)

    # ── Factory methods ────────────────────────────────────────────────────────

    @classmethod
    def with_stub(cls, repository: VisionRepository) -> "VisionOrchestrator":
        """
        Create an orchestrator backed by the StubDetector.

        Use in:
          • Unit/integration tests.
          • Local development without a GPU.
          • Health-check endpoints.
        """
        from app.modules.vision.infrastructure.detector import StubDetector

        return cls(detector=StubDetector(), repository=repository)

    @classmethod
    def with_yolo(cls, repository: VisionRepository) -> "VisionOrchestrator":
        """
        Create an orchestrator backed by the production YOLODetector.

        The model is loaded lazily on first inference call.
        """
        from app.modules.vision.infrastructure.yolo_detector import YOLODetector

        return cls(detector=YOLODetector(), repository=repository)
