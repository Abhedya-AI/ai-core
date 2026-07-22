"""
domain/__init__.py — Re-exports for convenient domain imports.

Usage (application layer):
    from app.modules.vision.domain import (
        Detection, Hazard, VisionEvent,
        BoundingBox, RiskScore,
        HazardType, RiskLevel, DetectionStatus,
        VisionRepository, RepositoryError,
    )
"""

from app.modules.vision.domain.entities import Detection, Hazard, VisionEvent
from app.modules.vision.domain.enums import DetectionStatus, HazardType, RiskLevel
from app.modules.vision.domain.repository import RepositoryError, VisionRepository
from app.modules.vision.domain.value_objects import BoundingBox, RiskScore

__all__ = [
    # entities
    "Detection",
    "Hazard",
    "VisionEvent",
    # value objects
    "BoundingBox",
    "RiskScore",
    # enums
    "HazardType",
    "RiskLevel",
    "DetectionStatus",
    # repository
    "VisionRepository",
    "RepositoryError",
]
