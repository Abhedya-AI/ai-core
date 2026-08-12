"""
vision/application/camera/camera_service.py — Camera Service.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from app.core.logging import get_logger
from app.modules.vision.domain.entities.camera import Camera
from app.modules.vision.domain.entities.camera_group import CameraGroup
from app.modules.vision.domain.entities.camera_health import CameraHealth
from app.modules.vision.domain.enums.camera_type import CameraType
from app.modules.vision.domain.enums.camera_status import CameraStatus
from app.modules.vision.application.events.knowledge_graph_sync import VisionKnowledgeGraphSync

log = get_logger("vision.application.camera_service")

class CreateCameraRequest(BaseModel):
    name: str
    camera_type: CameraType = CameraType.IP
    stream_url: str | None = None
    location: str
    zone_id: str | None = None
    plant_id: str | None = None
    group_id: str | None = None
    username: str | None = None
    fps_limit: int = 5
    resolution: str = '1280x720'
    metadata: dict = Field(default_factory=dict)

class UpdateCameraRequest(BaseModel):
    name: str | None = None
    stream_url: str | None = None
    location: str | None = None
    zone_id: str | None = None
    group_id: str | None = None
    fps_limit: int | None = None
    resolution: str | None = None
    is_active: bool | None = None
    metadata: dict | None = None

class CameraService:
    def __init__(
        self,
        camera_repo: Any,
        kg_sync: VisionKnowledgeGraphSync,
    ) -> None:
        self._repo = camera_repo
        self._kg = kg_sync

    async def register_camera(self, req: CreateCameraRequest) -> Camera:
        cam = Camera(
            id=str(uuid.uuid4()),
            name=req.name,
            camera_type=req.camera_type,
            stream_url=req.stream_url,
            location=req.location,
            zone_id=req.zone_id,
            plant_id=req.plant_id,
            group_id=req.group_id,
            fps_limit=req.fps_limit,
            resolution=req.resolution,
            health_status=CameraStatus.OFFLINE,
            is_active=True,
            metadata=req.metadata,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await self._repo.save_camera(cam)
        await self._kg.sync_camera(cam)
        log.info(f"Registered camera {cam.id}")
        return cam

    async def get_camera(self, camera_id: str) -> Camera | None:
        return await self._repo.get_camera(camera_id)

    async def list_cameras(self, zone_id=None, group_id=None, status=None, active_only=False, limit=100, offset=0) -> list[Camera]:
        return await self._repo.list_cameras(zone_id=zone_id, group_id=group_id, status=status, active_only=active_only, limit=limit, offset=offset)

    async def update_camera(self, camera_id: str, req: UpdateCameraRequest) -> Camera | None:
        cam = await self._repo.get_camera(camera_id)
        if not cam:
            return None
        
        update_data = req.model_dump(exclude_unset=True)
        cam = cam.model_copy(update=update_data)
        
        await self._repo.save_camera(cam)
        await self._kg.sync_camera(cam)
        return cam

    async def delete_camera(self, camera_id: str) -> bool:
        await self._repo.delete_camera(camera_id)
        return True

    async def deregister_camera(self, camera_id: str) -> bool:
        return await self.delete_camera(camera_id)

    async def mark_camera_online(self, camera_id: str) -> Camera | None:
        cam = await self._repo.get_camera(camera_id)
        if not cam:
            return None
        updated = cam.mark_online()
        await self._repo.save_camera(updated)
        await self._kg.sync_camera(updated)
        return updated

    async def mark_camera_offline(self, camera_id: str) -> Camera | None:
        cam = await self._repo.get_camera(camera_id)
        if not cam:
            return None
        updated = cam.mark_offline()
        await self._repo.save_camera(updated)
        await self._kg.sync_camera(updated)
        return updated

    async def update_heartbeat(self, camera_id: str) -> bool:
        cam = await self._repo.get_camera(camera_id)
        if not cam:
            return False
        updated = cam.update_last_seen().mark_online()
        await self._repo.save_camera(updated)
        return True

    async def handle_heartbeat(self, camera_id: str) -> bool:
        return await self.update_heartbeat(camera_id)

    async def create_group(self, name: str, zone_id: str | None, plant_id: str | None, description: str = '') -> CameraGroup:
        grp = CameraGroup(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            zone_id=zone_id,
            plant_id=plant_id,
            camera_ids=[]
        )
        await self._repo.save_group(grp)
        return grp

    async def add_camera_to_group(self, group_id: str, camera_id: str) -> CameraGroup | None:
        grp = await self._repo.get_group(group_id)
        if grp and camera_id not in grp.camera_ids:
            updated = grp.add_camera(camera_id)
            await self._repo.save_group(updated)
            await self._kg.sync_camera_group(updated)
            return updated
        return grp

    async def get_group(self, group_id: str) -> CameraGroup | None:
        return await self._repo.get_group(group_id)

    async def list_groups(self) -> list[CameraGroup]:
        return await self._repo.list_groups()
