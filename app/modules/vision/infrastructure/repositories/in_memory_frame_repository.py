"""
vision/infrastructure/repositories/in_memory_frame_repository.py

In-memory implementation of FrameRepository for testing and development.
"""
from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.repositories.frame_repository import FrameRepository
from app.modules.vision.domain.entities.frame import Frame
from app.modules.vision.domain.entities.frame_metadata import FrameMetadata

log = get_logger("vision.infrastructure.repos.frame")

class InMemoryFrameRepository(FrameRepository):
    def __init__(self):
        self._frames: dict[str, Frame] = {}
        self._metadata: dict[str, FrameMetadata] = {}
        self._lock = asyncio.Lock()

    async def save_frame(self, frame: Frame) -> Frame:
        async with self._lock:
            self._frames[frame.id] = frame
        return frame

    async def get_frame(self, frame_id: str) -> Frame | None:
        async with self._lock:
            return self._frames.get(frame_id)

    async def save_metadata(self, metadata: FrameMetadata) -> FrameMetadata:
        async with self._lock:
            self._metadata[metadata.frame_id] = metadata
        return metadata

    async def get_metadata(self, frame_id: str) -> FrameMetadata | None:
        async with self._lock:
            return self._metadata.get(frame_id)

    async def list_frames_by_camera(self, camera_id: str, limit: int = 50, offset: int = 0) -> list[Frame]:
        async with self._lock:
            frames = [f for f in self._frames.values() if f.camera_id == camera_id]
            frames.sort(key=lambda f: f.captured_at, reverse=True)
            return frames[offset:offset+limit]

    async def list_frames_in_window(self, camera_id: str, start: datetime, end: datetime) -> list[Frame]:
        async with self._lock:
            frames = [
                f for f in self._frames.values() 
                if f.camera_id == camera_id and start <= f.captured_at <= end
            ]
            frames.sort(key=lambda f: f.captured_at)
            return frames

    async def delete_old_frames(self, camera_id: str, before: datetime) -> int:
        async with self._lock:
            to_delete = [
                f_id for f_id, f in self._frames.items() 
                if f.camera_id == camera_id and f.captured_at < before
            ]
            for f_id in to_delete:
                del self._frames[f_id]
                if f_id in self._metadata:
                    del self._metadata[f_id]
            return len(to_delete)
