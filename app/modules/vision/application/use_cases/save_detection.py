"""
application/use_cases/save_detection.py — SaveDetectionUseCase

Responsibility (ONE thing only)
────────────────────────────────
Persist a VisionEvent aggregate (with its detections) to the repository.

This use case knows nothing about:
  • Images or detectors     (→ AnalyzeFrameUseCase)
  • Risk calculation        (→ CalculateRiskUseCase)
  • Kafka                   (→ PublishEventUseCase)

It answers exactly one question:
  "Is this VisionEvent durably stored?"
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.application.exceptions import PersistenceError
from app.modules.vision.domain.entities import VisionEvent
from app.modules.vision.domain.repositories import VisionRepository

log = get_logger("vision.use_cases.save_detection")


class SaveDetectionUseCase:
    """
    Persists a VisionEvent via the repository contract.

    Parameters (injected)
    ─────────────────────
    repository  Any VisionRepository implementation (Postgres, in-memory, …).

    Usage
    ─────
        saved_event = await SaveDetectionUseCase(repository).execute(event)
    """

    def __init__(self, repository: VisionRepository) -> None:
        self._repository = repository

    async def execute(self, event: VisionEvent) -> VisionEvent:
        """
        Persist the VisionEvent aggregate and return the saved instance.

        Raises
        ──────
        PersistenceError  If the repository operation fails.
        """
        log.info(
            f"SaveDetectionUseCase: saving event_id={event.event_id} "
            f"camera={event.camera_id} detections={len(event.detections)}"
        )

        try:
            saved = await self._repository.save_event(event)
        except Exception as exc:
            raise PersistenceError(
                f"Failed to save VisionEvent {event.event_id}: {exc}",
                detail=str(exc),
            ) from exc

        log.info(f"SaveDetectionUseCase: event {saved.event_id} persisted ✓")
        return saved
