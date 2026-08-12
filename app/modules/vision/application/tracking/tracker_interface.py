"""
vision/application/tracking/tracker_interface.py — Base Tracker Interface.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from app.modules.vision.domain.entities.detection import Detection
from app.modules.vision.domain.entities.tracking_object import TrackingObject

class BaseTracker(ABC):
    @abstractmethod
    def update(self, detections: list[Detection], frame_id: str, timestamp: datetime) -> list[TrackingObject]:
        pass

    @abstractmethod
    def get_active_tracks(self) -> list[TrackingObject]:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @property
    @abstractmethod
    def tracker_name(self) -> str:
        pass
