from .camera_repository import CameraRepository
from .vision_repository import VisionRepository


class RepositoryError(Exception):
    """Base exception for all repository-related failures."""
    pass


__all__ = [
    "VisionRepository",
    "CameraRepository",
    "RepositoryError",
]
