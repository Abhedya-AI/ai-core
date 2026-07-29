"""
application/use_cases/analyze_frame.py — AnalyzeFrameUseCase

Responsibility (ONE thing only)
────────────────────────────────
Receive raw image bytes → run the detector → map raw results to
domain Detections → return a FrameAnalysisResult DTO.

This use case knows nothing about:
  • Risk scores          (→ CalculateRiskUseCase)
  • Database             (→ SaveDetectionUseCase)
  • Kafka                (→ PublishEventUseCase)
  • VisionEvent assembly (→ ProcessDetectionUseCase)

It answers exactly one question:
  "What objects are visible in this image?"

Dependency injection
────────────────────
FrameDetector is an abstract interface. Concrete implementations:
  • YOLODetector  (infrastructure/yolo_detector.py)
  • StubDetector  (infrastructure/detector.py) — for tests / dev
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from app.core.logging import get_logger
from app.modules.vision.application.dto.analyze_response import FrameAnalysisResult
from app.modules.vision.application.exceptions import (
    DetectorUnavailableError,
    FrameReadError,
)
from app.modules.vision.domain.entities import Detection
from app.modules.vision.schemas.request import AnalyzeFrameRequest

log = get_logger("vision.use_cases.analyze_frame")


# ── Port interface ─────────────────────────────────────────────────────────────

class FrameDetector(ABC):
    """
    Abstract detector port.

    Concrete implementations live in infrastructure/ and are injected
    at startup — the use case never imports them directly.
    """

    #: Override in concrete implementations to expose the model identifier.
    model_version: str = "unknown"

    @abstractmethod
    async def detect(
        self,
        image_bytes:    bytes,
        frame_id:       str,
        camera_id:      str,
        min_confidence: float = 0.4,
    ) -> list[Detection]:
        """Run inference. Return a list of domain Detection objects."""


# ── Use case ───────────────────────────────────────────────────────────────────

class AnalyzeFrameUseCase:
    """
    Runs the detector and returns a FrameAnalysisResult.

    Parameters (injected)
    ─────────────────────
    detector    Concrete FrameDetector implementation.

    Usage
    ─────
        result = await AnalyzeFrameUseCase(detector).execute(
            image_bytes, request
        )
        # result.detections → list[Detection]
        # result.processing_time_ms → float
    """

    def __init__(self, detector: FrameDetector) -> None:
        self._detector = detector

    async def execute(
        self,
        image_bytes: bytes,
        request:     AnalyzeFrameRequest,
    ) -> FrameAnalysisResult:
        """
        Detect hazards in a single frame.

        Raises
        ──────
        FrameReadError              If image_bytes is empty.
        DetectorUnavailableError    If the detector raises an unexpected error.
        """
        import uuid

        if not image_bytes:
            raise FrameReadError("Image bytes are empty — nothing to analyse.")

        frame_id  = request.frame_id or str(uuid.uuid4())
        camera_id = request.camera_id

        log.info(
            f"AnalyzeFrameUseCase: camera={camera_id} "
            f"frame={frame_id} size={len(image_bytes)}B"
        )

        t0 = time.monotonic()

        try:
            detections: list[Detection] = await self._detector.detect(
                image_bytes=image_bytes,
                frame_id=frame_id,
                camera_id=camera_id,
                min_confidence=request.min_confidence,
            )
        except Exception as exc:
            raise DetectorUnavailableError(
                f"Detector failed on frame {frame_id}: {exc}",
                detail=str(exc),
            ) from exc

        processing_time_ms = (time.monotonic() - t0) * 1000

        log.info(
            f"AnalyzeFrameUseCase: {len(detections)} detection(s) in "
            f"{processing_time_ms:.1f}ms  model={self._detector.model_version}"
        )

        return FrameAnalysisResult(
            frame_id=frame_id,
            camera_id=camera_id,
            processing_time_ms=processing_time_ms,
            detections=detections,
            model_version=self._detector.model_version,
        )
