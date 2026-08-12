from __future__ import annotations
from typing import Any
import time
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.digital_twin.application.synchronization.base import AbstractSyncEngine, SyncResult, SyncConflictResolver

log = get_logger(__name__)

class VisionSyncEngine(AbstractSyncEngine):
    def __init__(self):
        try:
            from app.modules.vision.services.vision_service import VisionService
            self._vision_service = VisionService()
        except ImportError:
            self._vision_service = None
            log.warning("VisionService not available. Falling back to context data.")
        self._resolver = SyncConflictResolver()

    async def sync(self, twin_id: str, context: dict[str, Any]) -> SyncResult:
        t0 = time.perf_counter()
        entity_updates: dict[str, Any] = {}
        error_message = None
        status = "COMPLETED"
        
        try:
            if self._vision_service and hasattr(self._vision_service, "get_camera_states"):
                cameras = await self._vision_service.get_camera_states(twin_id)
                for cam in cameras:
                    cam_id = cam.get("camera_id")
                    if cam_id:
                        entity_updates[cam_id] = {
                            "camera_id": cam_id,
                            "is_online": cam.get("is_online", True),
                            "detected_workers": cam.get("detected_workers", []),
                            "detected_violations": cam.get("detected_violations", []),
                            "occupancy": cam.get("occupancy", 0),
                            "ppe_compliance_rate": cam.get("ppe_compliance_rate", 1.0),
                            "fire_detected": cam.get("fire_detected", False),
                            "smoke_detected": cam.get("smoke_detected", False),
                            "timestamp": cam.get("timestamp", datetime.now(timezone.utc).isoformat())
                        }
            
            context_data = context.get("vision_data", {})
            for cam_id, data in context_data.items():
                existing = entity_updates.get(cam_id, {})
                entity_updates[cam_id] = self._resolver.resolve(existing, data, self.get_source())
                
        except Exception as e:
            error_message = str(e)
            status = "FAILED"
            log.error(f"VisionSyncEngine sync failed: {e}")
            
        latency_ms = (time.perf_counter() - t0) * 1000
        return SyncResult(
            source=self.get_source(),
            status=status,
            entity_updates=entity_updates,
            update_count=len(entity_updates),
            error_message=error_message,
            latency_ms=latency_ms,
            synced_at=datetime.now(timezone.utc).isoformat()
        )

    async def incremental_sync(self, twin_id: str, since: str, context: dict[str, Any]) -> SyncResult:
        # For simplicity, fallback to full sync in this implementation
        return await self.sync(twin_id, context)

    def get_source(self) -> str:
        return "VISION"

    def is_available(self) -> bool:
        return self._vision_service is not None
