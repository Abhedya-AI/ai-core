"""
vision/application/events/knowledge_graph_sync.py — Vision Knowledge Graph Synchronizer.
"""
from __future__ import annotations
import asyncio
from app.core.logging import get_logger
from app.modules.vision.infrastructure.vision_neo4j_repository import VisionNeo4jRepository
from app.modules.vision.domain.entities.camera import Camera
from app.modules.vision.domain.entities.detection_event import DetectionEvent
from app.modules.vision.domain.entities.frame import Frame
from app.modules.vision.domain.entities.frame_metadata import FrameMetadata
from app.modules.vision.domain.entities.tracking_object import TrackingObject
from app.modules.vision.domain.entities.vision_alert import VisionAlert
from app.modules.vision.domain.entities.camera_group import CameraGroup

log = get_logger("vision.application.events.kg_sync")

class VisionKnowledgeGraphSync:
    def __init__(self, neo4j_repo: VisionNeo4jRepository) -> None:
        self._repo = neo4j_repo

    async def _safe_execute(self, task):
        try:
            await task
        except Exception as exc:
            log.warning(f"KG sync failed: {exc}")

    async def sync_camera(self, camera: Camera) -> None:
        log.info(f"KG sync: camera {camera.id}")
        asyncio.create_task(self._safe_execute(self._repo.upsert_camera_node(camera)))

    async def sync_detection_event(self, det_event: DetectionEvent, frame: Frame | None = None) -> None:
        tasks = [self._repo.upsert_detection_node(det_event)]
        if frame is not None:
            tasks.append(self._repo.upsert_frame_node(frame))
        asyncio.create_task(asyncio.gather(*tasks, return_exceptions=True))

    async def sync_tracking_object(self, track: TrackingObject) -> None:
        asyncio.create_task(self._safe_execute(self._repo.upsert_tracking_node(track)))

    async def sync_alert(self, alert: VisionAlert) -> None:
        asyncio.create_task(self._safe_execute(self._repo.upsert_alert_node(alert)))

    async def sync_camera_group(self, group: CameraGroup) -> None:
        if not group.camera_ids:
            return
        tasks = []
        for i in range(len(group.camera_ids) - 1):
            tasks.append(self._repo.link_camera_group(group.camera_ids[i], group.camera_ids[i+1]))
        if tasks:
            asyncio.create_task(asyncio.gather(*tasks, return_exceptions=True))

    async def get_zone_context(self, zone_id: str) -> dict:
        summary = await self._repo.get_zone_risk_summary(zone_id)
        recent_detections = await self._repo.get_recent_detections_for_zone(zone_id)
        return {
            "summary": summary,
            "recent_detections": recent_detections
        }

    async def get_camera_context(self, camera_id: str) -> dict:
        return await self._repo.get_camera_context(camera_id)
