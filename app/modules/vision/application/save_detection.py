"""
application/save_detection.py — backward-compatibility shim.

The canonical implementation is now at:
    application/use_cases/save_detection.py

This file re-exports everything so existing imports keep working.
"""

from app.modules.vision.application.use_cases.save_detection import SaveDetectionUseCase
from app.modules.vision.application.exceptions import PersistenceError

# Legacy function alias kept for any code that called save_detection() directly
async def save_detection(detection, repository):
    """Deprecated function shim — use SaveDetectionUseCase directly."""
    from app.modules.vision.domain.entities import VisionEvent
    # If called with a Detection (old API), wrap it in a minimal event call
    raise NotImplementedError(
        "save_detection() is deprecated. Use SaveDetectionUseCase(repository).execute(event)."
    )


# Legacy exception alias
class SaveDetectionError(PersistenceError):
    """Deprecated alias for PersistenceError."""
    pass


__all__ = [
    "SaveDetectionUseCase",
    "SaveDetectionError",
    "save_detection",
]
