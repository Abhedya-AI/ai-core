"""
vision/infrastructure/repositories/in_memory_tracking_repository.py

In-memory implementation of TrackingRepository for testing and development.
"""
from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.repositories.tracking_repository import TrackingRepository
from app.modules.vision.domain.entities.tracking_object import TrackingObject
from app.modules.vision.domain.entities.tracking_history import TrackingHistory

log = get_logger("vision.infrastructure.repos.tracking")

class InMemoryTrackingRepository(TrackingRepository):
    def __init__(self):
        self._tracks: dict[str, TrackingObject] = {}
        self._history: dict[str, TrackingHistory] = {}
        self._lock = asyncio.Lock()

    async def save_track(self, track: TrackingObject) -> TrackingObject:
        async with self._lock:
            self._tracks[track.track_id] = track
        return track

    async def get_track(self, track_id: str) -> TrackingObject | None:
        async with self._lock:
            return self._tracks.get(track_id)

    async def update_track(self, track: TrackingObject) -> TrackingObject:
        async with self._lock:
            self._tracks[track.track_id] = track
        return track

    async def list_active_tracks(self, camera_id: str | None = None) -> list[TrackingObject]:
        async with self._lock:
            tracks = [t for t in self._tracks.values() if t.is_active]
            if camera_id:
                tracks = [t for t in tracks if t.camera_id == camera_id]
            tracks.sort(key=lambda t: t.first_seen_at, reverse=True)
            return tracks

    async def list_tracks_by_camera(self, camera_id: str, limit: int = 50, offset: int = 0) -> list[TrackingObject]:
        async with self._lock:
            tracks = [t for t in self._tracks.values() if t.camera_id == camera_id]
            return tracks[offset:offset + limit]

    async def end_track(self, track_id: str) -> None:
        async with self._lock:
            if track_id in self._tracks:
                self._tracks[track_id] = self._tracks[track_id].deactivate()

    async def save_history(self, history: TrackingHistory) -> TrackingHistory:
        async with self._lock:
            self._history[history.track_id] = history
        return history

    async def get_history(self, track_id: str) -> TrackingHistory | None:
        async with self._lock:
            return self._history.get(track_id)
