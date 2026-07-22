"""
application/analyze_frame.py — AnalyzeFrameUseCase: the central orchestrator.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.vision.application.publish_event import (
    PublishEventError,
    publish_vision_event,
)
from app.modules.vision.application.save_detection import (
    SaveDetectionError,
    save_detection,
)
from app.modules.vision.domain.entities import Detection, VisionEvent
from app.modules.vision.domain.repositories import VisionRepository
from app.modules.vision.schemas.request import AnalyzeFrameRequest

log = get_logger("vision.analyze_frame")


# ── Port interfaces (typing only — implementations injected) ──────────────────

class FrameDetector:
    """
    Abstract interface for vision detectors.
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
        """
        return []


# ── Use-case ──────────────────────────────────────────────────────────────────

class AnalyzeFrameUseCase:
    """
    Central orchestrator for the Vision Intelligence module.
    """

    def __init__(
        self,
        detector:    FrameDetector,
        repository:  VisionRepository,
    ) -> None:
        self._detector    = detector
        self._repository  = repository

    async def execute(
        self,
        image_bytes: bytes,
        request:     AnalyzeFrameRequest,
    ) -> list[VisionEvent]:
        """
        Run the full analysis pipeline for a single frame.

        Parameters
        ──────────
        image_bytes Raw bytes of the uploaded image.
        request     Validated API request carrying metadata.

        Returns
        ───────
        list[VisionEvent] — the events published for the frame detections.
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

        events: list[VisionEvent] = []

        for det in detections:
            # ── Step 2: Save Detection ────────────────────────────────────────
            try:
                await save_detection(det, self._repository)
            except SaveDetectionError as exc:
                log.warning(f"Persistence failed for detection {det.id} (non-fatal): {exc}")

            # ── Step 3: Assemble VisionEvent ──────────────────────────────────
            event = VisionEvent(
                event_id=uuid.uuid4(),
                detection_id=det.id,
                camera_id=det.camera_id,
                hazard_type=det.hazard_type,
                risk_level=det.risk.level,
                confidence=det.confidence,
                occurred_at=datetime.now(tz=timezone.utc),
            )
            events.append(event)

            # ── Step 4: Publish Event ─────────────────────────────────────────
            try:
                await publish_vision_event(event)
            except PublishEventError as exc:
                log.warning(f"Event publish failed for event {event.event_id} (non-fatal): {exc}")

        log.info(f"Frame analysis completed. Generated {len(events)} event(s).")
        return events
