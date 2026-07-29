"""
application/use_cases/process_detection.py — ProcessDetectionUseCase

The Orchestrator
────────────────
This is the ONLY class that knows the complete detection pipeline.
It chains the four single-responsibility use cases in order:

    AnalyzeFrameUseCase      image → detections + metrics
          │
    CalculateRiskUseCase     detections → risk_score + hazards
          │
    (assemble VisionEvent)
          │
    SaveDetectionUseCase     VisionEvent → persisted VisionEvent
          │
    PublishEventUseCase      VisionEvent → Kafka (best-effort)
          │
    return FrameAnalysisResult

Error handling
──────────────
• FrameReadError / DetectorUnavailableError → propagated (fail the request).
• RiskCalculationError                      → propagated (fail the request).
• PersistenceError                          → propagated (fail the request).
• EventPublishingError                      → logged as WARNING, NOT propagated.
  Kafka is best-effort. The event is already stored; loss of the publish
  must not roll back the analysis.

Single log statement
────────────────────
One INFO log per execution at the end summarising the full result.
Individual use cases log their own single-line summaries at INFO level.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.application.dto.analyze_response import FrameAnalysisResult
from app.modules.vision.application.exceptions import EventPublishingError
from app.modules.vision.application.use_cases.analyze_frame import (
    AnalyzeFrameUseCase,
    FrameDetector,
)
from app.modules.vision.application.use_cases.calculate_risk import CalculateRiskUseCase
from app.modules.vision.application.use_cases.publish_event import PublishEventUseCase
from app.modules.vision.application.use_cases.save_detection import SaveDetectionUseCase
from app.modules.vision.domain.entities import VisionEvent
from app.modules.vision.domain.repositories import VisionRepository
from app.modules.vision.schemas.request import AnalyzeFrameRequest

log = get_logger("vision.use_cases.process_detection")


class ProcessDetectionUseCase:
    """
    Full detection pipeline — the single entry point for the Vision API.

    Parameters (injected)
    ─────────────────────
    detector    Concrete FrameDetector (YOLO, Stub, …).
    repository  Concrete VisionRepository (Postgres, in-memory, …).

    Usage
    ─────
        result = await ProcessDetectionUseCase(detector, repo).execute(
            image_bytes, request
        )
    """

    def __init__(
        self,
        detector:   FrameDetector,
        repository: VisionRepository,
    ) -> None:
        self._analyze   = AnalyzeFrameUseCase(detector)
        self._risk      = CalculateRiskUseCase()
        self._save      = SaveDetectionUseCase(repository)
        self._publish   = PublishEventUseCase()

    async def execute(
        self,
        image_bytes: bytes,
        request:     AnalyzeFrameRequest,
    ) -> FrameAnalysisResult:
        """
        Run the complete detection → risk → save → publish pipeline.

        Returns
        ───────
        FrameAnalysisResult with all fields populated, including the
        persisted VisionEvent.
        """

        # ── Step 1: Detect ─────────────────────────────────────────────────────
        frame_result: FrameAnalysisResult = await self._analyze.execute(
            image_bytes, request
        )

        # ── Step 2: Calculate risk ──────────────────────────────────────────────
        risk_score, hazards = self._risk.execute(frame_result.detections)

        # ── Step 3: Assemble VisionEvent aggregate ──────────────────────────────
        event = VisionEvent(
            camera_id=frame_result.camera_id,
            frame_id=frame_result.frame_id,
            detections=frame_result.detections,
            hazards=hazards,
            risk_score=risk_score,
        )

        # ── Step 4: Persist ─────────────────────────────────────────────────────
        saved_event = await self._save.execute(event)

        # ── Step 5: Publish (best-effort) ───────────────────────────────────────
        try:
            await self._publish.execute(saved_event)
        except EventPublishingError as exc:
            log.warning(
                f"ProcessDetectionUseCase: Kafka publish failed — "
                f"event {saved_event.event_id} is persisted but NOT broadcast. "
                f"Reason: {exc.message}"
            )

        # ── Step 6: Assemble final FrameAnalysisResult ──────────────────────────
        result = FrameAnalysisResult(
            frame_id=frame_result.frame_id,
            camera_id=frame_result.camera_id,
            processing_time_ms=frame_result.processing_time_ms,
            detections=frame_result.detections,
            hazards=hazards,
            risk_score=risk_score,
            highest_risk=risk_score.level,
            model_version=frame_result.model_version,
            event=saved_event,
        )

        log.info(result.summary())
        return result
