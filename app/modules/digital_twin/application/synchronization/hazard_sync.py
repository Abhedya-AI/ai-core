from __future__ import annotations
from typing import Any
import time
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.digital_twin.application.synchronization.base import AbstractSyncEngine, SyncResult, SyncConflictResolver

log = get_logger(__name__)

class HazardSyncEngine(AbstractSyncEngine):
    def __init__(self):
        try:
            from app.modules.hazard_propagation.application.services.hazard_orchestration_service import HazardOrchestrationService
            self._hazard_service = HazardOrchestrationService()
        except ImportError:
            self._hazard_service = None
            log.warning("HazardOrchestrationService not available. Falling back to context data.")
        self._resolver = SyncConflictResolver()

    async def sync(self, twin_id: str, context: dict[str, Any]) -> SyncResult:
        t0 = time.perf_counter()
        entity_updates: dict[str, Any] = {}
        error_message = None
        status = "COMPLETED"
        
        try:
            if self._hazard_service and hasattr(self._hazard_service, "get_active_hazards"):
                hazards = await self._hazard_service.get_active_hazards(twin_id)
                for h in hazards:
                    h_id = h.get("hazard_id")
                    if h_id:
                        entity_updates[h_id] = h
                        
                    # Also update zones affected by hazard
                    zones = h.get("affected_zones", [])
                    for z_id in zones:
                        if z_id not in entity_updates:
                            entity_updates[z_id] = {"is_hazard_active": True, "hazard_ids": []}
                        if h_id not in entity_updates[z_id]["hazard_ids"]:
                            entity_updates[z_id]["hazard_ids"].append(h_id)
                            
            context_data = context.get("hazard_data", {})
            for entity_id, data in context_data.items():
                existing = entity_updates.get(entity_id, {})
                entity_updates[entity_id] = self._resolver.resolve(existing, data, self.get_source())
                
        except Exception as e:
            error_message = str(e)
            status = "FAILED"
            log.error(f"HazardSyncEngine sync failed: {e}")
            
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
        return await self.sync(twin_id, context)

    def get_source(self) -> str:
        return "HAZARD"

    def is_available(self) -> bool:
        return self._hazard_service is not None
