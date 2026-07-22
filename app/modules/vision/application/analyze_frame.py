"""
application/analyze_frame.py — AnalyzeFrameUseCase: the central orchestrator.

This is the only use-case that coordinates all other components:

    Image bytes
        │
        ▼
    Detector  (infrastructure — YOLO, RT-DETR, …)
        │  raw detections
        ▼
    Mapper    (infrastructure — maps raw → domain Detection)
        │  domain Detections
        ▼
    RiskEngine  (application — calculate_risk.py)
        │  RiskScore + Hazards
        ▼
    VisionEvent  (assembled here)
        │
        ├──▶ Repository.save_event()   (save_detection.py)
        │
        ├──▶ EventBus.publish()        (publish_event.py)
        │
        └──▶ return VisionEvent

Dependency injection
────────────────────
The use-case receives its dependencies (detector, mapper, repository)
as constructor arguments.  This makes it testable without any mocking
framework — just pass in stubs.

In Milestone 1 the detector is a stub that returns empty detections;
wiring the real YOLO implementation happens in Milestone 2.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.vision.application.calculate_risk import RiskEngine
from app.modules.vision.application.publish_event import (
    PublishEventError,
    publish_vision_event,
)
from app.modules.vision.application.save_detection import (
    SaveDetectionError,
    save_vision_event,
)
from app.modules.vision.domain.entities import Detection, VisionEvent
from app.modules.vision.domain.repository import VisionRepository
from app.modules.vision.schemas.request import AnalyzeFrameRequest

log = get_logger("vision.analyze_frame")


# ── Port interfaces (typing only — implementations injected) ──────────────────

class FrameDetector:
    """
    Abstract interface for vision detectors.

    Concrete implementations:
        infrastructure/yolo_detector.py  (Milestone 2)

    The method signature is deliberately simple: bytes in, detections out.
    Pre/post-processing lives inside the implementation.
    """

    async def detect(
        self,
        image_bytes: bytes,
        frame_id: str,
        camera_id: str,
        min_confidence: float = 0.4,
    ) -> list[Detection]:
        """
        Run inference and return domain Detections.

        Implementations must:
          1. Pre-process the image.
          2. Run the model.
          3. Map raw outputs to domain Detection objects via the mapper.
          4. Filter by min_confidence.
          5. Return the list (may be empty).

        This base class returns an empty list — used as a stub in
        Milestone 1 so routes can be exercised without a real model.
        """
        return []


# ── Use-case ──────────────────────────────────────────────────────────────────

class AnalyzeFrameUseCase:
    """
    Central orchestrator for the Vision Intelligence module.

    Constructor parameters
    ──────────────────────
    detector    A FrameDetector implementation.
    repository  A VisionRepository implementation.
    risk_engine A RiskEngine instance.

    Usage (in a FastAPI route via dependency injection):
        use_case = AnalyzeFrameUseCase(
            detector=YOLODetector(...),
            repository=PostgresVisionRepository(session),
        )
        event = await use_case.execute(image_bytes, request)
    """

    def __init__(
        self,
        detector:    FrameDetector,
        repository:  VisionRepository,
        risk_engine: RiskEngine | None = None,
    ) -> None:
        self._detector    = detector
        self._repository  = repository
        self._risk_engine = risk_engine or RiskEngine()

    async def execute(
        self,
        image_bytes: bytes,
        request:     AnalyzeFrameRequest,
    ) -> VisionEvent:
        """
        Run the full analysis pipeline for a single frame.

        Parameters
        ──────────
        image_bytes Raw bytes of the uploaded image.
        request     Validated API request carrying metadata.

        Returns
        ───────
        VisionEvent — the complete analysis result.
        """
        frame_id  = request.frame_id or str(uuid.uuid4())
        camera_id = request.camera_id

        log.info(
            f"AnalyzeFrameUseCase.execute() "
            f"camera_id={camera_id} frame_id={frame_id} "
            f"image_size={len(image_bytes)} bytes"
        )

        # ── Step 1: Detect ────────────────────────────────────────────────────
        detections: list[Detection] = await self._detector.detect(
            image_bytes=image_bytes,
            frame_id=frame_id,
            camera_id=camera_id,
            min_confidence=request.min_confidence,
        )
        log.info(f"Detector returned {len(detections)} detection(s).")

        # ── Step 2: Risk calculation ──────────────────────────────────────────
        risk_score, hazards = self._risk_engine.calculate(detections)
        log.info(
            f"Risk: {risk_score.level.value} ({risk_score.value:.3f}) "
            f"hazards={len(hazards)}"
        )

        # ── Step 3: Assemble VisionEvent ──────────────────────────────────────
        event = VisionEvent(
            camera_id=camera_id,
            frame_id=frame_id,
            detections=detections,
            hazards=hazards,
            risk_score=risk_score,
            location=request.location,
            metadata=dict(request.metadata),
        )

        # ── Step 4: Persist ───────────────────────────────────────────────────
        try:
            event = await save_vision_event(event, self._repository)
        except SaveDetectionError as exc:
            # Persistence failure is logged but does not block the response
            log.warning(f"Persistence failed (non-fatal): {exc}")

        # ── Step 5: Publish ───────────────────────────────────────────────────
        try:
            await publish_vision_event(event)
        except PublishEventError as exc:
            # Publish failure is logged but does not block the response
            log.warning(f"Event publish failed (non-fatal): {exc}")

        log.info(event.summary())
        return event
