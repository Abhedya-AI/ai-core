from __future__ import annotations

class RepositoryError(Exception):
    """Base exception for vision repository errors."""
    pass

try:
    from app.modules.vision.domain.repositories.camera_repository import CameraRepository
except ImportError:
    pass
try:
    from app.modules.vision.domain.repositories.frame_repository import FrameRepository
except ImportError:
    pass
try:
    from app.modules.vision.domain.repositories.tracking_repository import TrackingRepository
except ImportError:
    pass
try:
    from app.modules.vision.domain.repositories.alert_repository import AlertRepository
except ImportError:
    pass

try:
    from app.modules.vision.domain.repositories.vision_repository import VisionRepository
except ImportError:
    pass

__all__ = [
    "RepositoryError",
    "CameraRepository",
    "FrameRepository",
    "TrackingRepository",
    "AlertRepository",
    "VisionRepository",
]
