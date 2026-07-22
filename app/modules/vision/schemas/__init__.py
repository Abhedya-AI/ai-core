"""
schemas/__init__.py — Re-exports for convenient schema imports.
"""

from app.modules.vision.schemas.request import AnalyzeFrameRequest, ListEventsRequest
from app.modules.vision.schemas.response import (
    AnalyzeFrameResponse,
    BoundingBoxSchema,
    DetectionSchema,
    GetEventResponse,
    HazardSchema,
    ListEventsResponse,
    RiskScoreSchema,
    VisionEventSchema,
)

__all__ = [
    # request
    "AnalyzeFrameRequest",
    "ListEventsRequest",
    # response
    "AnalyzeFrameResponse",
    "ListEventsResponse",
    "GetEventResponse",
    "VisionEventSchema",
    "DetectionSchema",
    "HazardSchema",
    "RiskScoreSchema",
    "BoundingBoxSchema",
]
