"""
vision/infrastructure/repositories/in_memory_camera_repository.py

In-memory implementation of CameraRepository for testing and development.
Thread-safe via asyncio locks. Fully implements all abstract methods.
"""
from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.modules.vision.domain.repositories.camera_repository import CameraRepository
from app.modules.vision.domain.entities.camera import Camera
from app.modules.vision.domain.entities.camera_group import CameraGroup
from app.modules.vision.domain.entities.camera_health import CameraHealth
from app.modules.vision.domain.enums.camera_status import CameraStatus

log = get_logger("vision.infrastructure.repos.camera")

class InMemoryCameraRepository(CameraRepository):
    def __init__(self):
        self._cameras: dict[str, Camera] = {}
        self._groups: dict[str, CameraGroup] = {}
        self._health: dict[str, CameraHealth] = {}
        self._lock = asyncio.Lock()

    # Legacy / base interface methods
    async def save(self, camera: Camera) -> Camera:
        return await self.save_camera(camera)

    async def get_by_id(self, camera_id: UUID | str) -> Camera | None:
        return await self.get_camera(str(camera_id))

    async def list_all(self) -> list[Camera]:
        return await self.list_cameras()

    async def update(self, camera: Camera) -> Camera:
        return await self.update_camera(camera)

    # Extended interface methods
    async def save_camera(self, camera: Camera) -> Camera:
        async with self._lock:
            self._cameras[str(camera.id)] = camera
        return camera

    async def get_camera(self, camera_id: str) -> Camera | None:
        async with self._lock:
            return self._cameras.get(str(camera_id))

    async def update_camera(self, camera: Camera) -> Camera:
        async with self._lock:
            self._cameras[str(camera.id)] = camera
        return camera

    async def delete_camera(self, camera_id: str) -> None:
        async with self._lock:
            self._cameras.pop(str(camera_id), None)

    async def list_cameras(
        self,
        zone_id: str | None = None,
        group_id: str | None = None,
        status: str | CameraStatus | None = None,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> list[Camera]:
        async with self._lock:
            cams = list(self._cameras.values())
            if zone_id:
                cams = [c for c in cams if c.zone_id == zone_id]
            if status:
                status_str = status.value if hasattr(status, 'value') else status
                cams = [c for c in cams if c.health_status.value == status_str or c.health_status == status]
            if active_only:
                cams = [c for c in cams if c.is_active]
            
            if group_id and group_id in self._groups:
                g = self._groups[group_id]
                cams = [c for c in cams if c.id in g.camera_ids]
            
            return cams[offset:offset+limit]

    async def list_by_zone(self, zone_id: str) -> list[Camera]:
        async with self._lock:
            return [c for c in self._cameras.values() if c.zone_id == zone_id]

    async def list_active(self) -> list[Camera]:
        async with self._lock:
            return [c for c in self._cameras.values() if c.is_active]

    async def save_group(self, group: CameraGroup) -> CameraGroup:
        async with self._lock:
            self._groups[group.id] = group
        return group

    async def get_group(self, group_id: str) -> CameraGroup | None:
        async with self._lock:
            return self._groups.get(group_id)

    async def list_groups(self) -> list[CameraGroup]:
        async with self._lock:
            return list(self._groups.values())

    async def save_health(self, health: CameraHealth) -> CameraHealth:
        async with self._lock:
            self._health[health.camera_id] = health
        return health

    async def get_health(self, camera_id: str) -> CameraHealth | None:
        async with self._lock:
            return self._health.get(camera_id)
