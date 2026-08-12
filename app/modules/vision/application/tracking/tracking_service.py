"""
vision/application/tracking/tracking_service.py — Tracking Service.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from app.core.logging import get_logger
from app.modules.vision.application.tracking.simple_iou_tracker import SimpleIoUTracker
from app.modules.vision.application.events.vision_event_publisher import VisionEventPublisher
from app.modules.vision.application.events.knowledge_graph_sync import VisionKnowledgeGraphSync
from app.modules.vision.domain.entities.detection import Detection
from app.modules.vision.domain.entities.tracking_object import TrackingObject, ZoneCrossing
from app.modules.vision.domain.entities.camera_zone import CameraZone
from app.modules.vision.domain.enums.stream_event_type import StreamEventType

log = get_logger("vision.application.tracking.tracking_service")

class TrackingService:
    def __init__(
        self,
        tracking_repo: Any,
        event_publisher: VisionEventPublisher,
        kg_sync: VisionKnowledgeGraphSync,
    ) -> None:
        self._repo = tracking_repo
        self._publisher = event_publisher
        self._kg = kg_sync
        self._trackers: dict[str, SimpleIoUTracker] = {}
        self._prev_track_ids: dict[str, set[str]] = {}

    def _get_centroid(self, bbox: dict) -> tuple[float, float]:
        if not bbox:
            return (0.0, 0.0)
        return ((bbox.get("x_min", 0) + bbox.get("x_max", 0)) / 2.0, (bbox.get("y_min", 0) + bbox.get("y_max", 0)) / 2.0)

    async def process_frame(self, camera_id: str, zone_id: str | None, detections: list[Detection], frame_id: str, zones: list[CameraZone]) -> list[TrackingObject]:
        if camera_id not in self._trackers:
            self._trackers[camera_id] = SimpleIoUTracker(camera_id)
        
        tracker = self._trackers[camera_id]
        now = datetime.now(timezone.utc)
        
        active_tracks = tracker.update(detections, frame_id, now)
        current_track_ids = {t.track_id for t in active_tracks}
        prev_track_ids = self._prev_track_ids.get(camera_id, set())
        
        for t in active_tracks:
            pass
            
        for t in active_tracks:
            if t.track_id not in prev_track_ids:
                await self._publisher.publish_tracking_event(t, StreamEventType.TRACKING_STARTED if hasattr(StreamEventType, 'TRACKING_STARTED') else "TRACKING_STARTED")
        
        for tid in prev_track_ids:
            if tid not in current_track_ids:
                pass

        self._prev_track_ids[camera_id] = current_track_ids
        
        for t in active_tracks:
            await self._repo.save(t)
            await self._kg.sync_tracking_object(t)
            
        return active_tracks

    async def end_all_tracks(self, camera_id: str) -> None:
        if camera_id in self._trackers:
            self._trackers[camera_id].reset()
            self._prev_track_ids[camera_id] = set()

    async def get_active_tracks(self, camera_id: str) -> list[TrackingObject]:
        if camera_id in self._trackers:
            return self._trackers[camera_id].get_active_tracks()
        return []

    async def get_track_history(self, track_id: str) -> Any | None:
        return await self._repo.get_history(track_id)
