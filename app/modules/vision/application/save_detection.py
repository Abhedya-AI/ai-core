"""
application/save_detection.py — Persistence use-case.

Responsibility: delegate VisionEvent persistence to the repository.

Design
──────
• Thin use-case — it validates preconditions, calls the repository,
  and translates RepositoryError into application-level exceptions.
• The application layer owns the transaction boundary decision (commit
  vs rollback) but delegates the mechanics to the repository.
• Async because the repository implementation uses asyncpg.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.domain.entities import VisionEvent
from app.modules.vision.domain.repository import RepositoryError, VisionRepository

log = get_logger("vision.save_detection")


class SaveDetectionError(Exception):
    """Raised when the persistence use-case cannot save a VisionEvent."""


async def save_vision_event(
    event: VisionEvent,
    repository: VisionRepository,
) -> VisionEvent:
    """
    Persist a VisionEvent and its detections.

    Parameters
    ──────────
    event       The domain aggregate to persist.
    repository  The concrete repository (injected by the route/use-case).

    Returns
    ───────
    The saved VisionEvent (may carry DB-assigned fields).

    Raises
    ──────
    SaveDetectionError  If the repository operation fails.
    """
    log.info(
        f"Persisting VisionEvent event_id={event.event_id} "
        f"camera_id={event.camera_id} "
        f"detections={event.detection_count}"
    )

    try:
        saved = await repository.save_event(event)
        log.info(f"VisionEvent {saved.event_id} persisted successfully.")
        return saved
    except RepositoryError as exc:
        log.error(f"Repository error while saving VisionEvent {event.event_id}: {exc}")
        raise SaveDetectionError(str(exc)) from exc
    except Exception as exc:
        log.error(f"Unexpected error while saving VisionEvent {event.event_id}: {exc}")
        raise SaveDetectionError(f"Unexpected persistence failure: {exc}") from exc
