"""
application/save_detection.py — Persistence use-case.

Responsibility: delegate Detection persistence to the repository.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.domain.entities import Detection
from app.modules.vision.domain.repositories import RepositoryError, VisionRepository

log = get_logger("vision.save_detection")


class SaveDetectionError(Exception):
    """Raised when the persistence use-case cannot save a Detection."""
    pass


async def save_detection(
    detection: Detection,
    repository: VisionRepository,
) -> Detection:
    """
    Persist a Detection.

    Parameters
    ──────────
    detection   The domain entity to persist.
    repository  The concrete repository (injected by the route/use-case).

    Returns
    ───────
    The saved Detection.

    Raises
    ──────
    SaveDetectionError  If the repository operation fails.
    """
    log.info(
        f"Persisting Detection detection_id={detection.id} "
        f"camera_id={detection.camera_id}"
    )

    try:
        saved = await repository.save(detection)
        log.info(f"Detection {saved.id} persisted successfully.")
        return saved
    except RepositoryError as exc:
        log.error(f"Repository error while saving Detection {detection.id}: {exc}")
        raise SaveDetectionError(str(exc)) from exc
    except Exception as exc:
        log.error(f"Unexpected error while saving Detection {detection.id}: {exc}")
        raise SaveDetectionError(f"Unexpected persistence failure: {exc}") from exc


async def save_vision_event(event: Any, repository: Any) -> Any:
    """Save vision event helper stub."""
    log.info("Persisting vision event")
    return event
