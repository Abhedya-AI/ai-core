"""
domain/repository.py — backward-compatibility shim.

The canonical location is domain/repositories/vision_repository.py.
This module re-exports VisionRepository so that any code importing from
the old path continues to work without modification.
"""

from app.modules.vision.domain.repositories.vision_repository import VisionRepository

__all__ = ["VisionRepository"]
