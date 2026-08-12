from __future__ import annotations
from typing import Any
import time
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.digital_twin.application.synchronization.base import AbstractSyncEngine, SyncResult, SyncConflictResolver

log = get_logger(__name__)

class SupervisorSyncEngine(AbstractSyncEngine):
    def __init__(self):
        try:
            from app.modules.supervisor.services.supervisor_service import SupervisorService
            self._supervisor_service = SupervisorService()
        except ImportError:
            self._supervisor_service = None
            log.warning("SupervisorService not available. Falling back to context data.")
        self._resolver = SyncConflictResolver()

    async def sync(self, twin_id: str, context: dict[str, Any]) -> SyncResult:
        t0 = time.perf_counter()
        entity_updates: dict[str, Any] = {}
        error_message = None
        status = "COMPLETED"
        
        try:
            if self._supervisor_service and hasattr(self._supervisor_service, "get_plant_decisions"):
                decisions = await self._supervisor_service.get_plant_decisions(twin_id)
                if decisions:
                    entity_updates["plant"] = {
                        "active_workflows": decisions.get("active_workflows", []),
                        "compliance_flags": decisions.get("compliance_flags", []),
                        "emergency_level": decisions.get("emergency_level", "NORMAL")
                    }
                    
            context_data = context.get("supervisor_data", {})
            for entity_id, data in context_data.items():
                existing = entity_updates.get(entity_id, {})
                entity_updates[entity_id] = self._resolver.resolve(existing, data, self.get_source())
                
        except Exception as e:
            error_message = str(e)
            status = "FAILED"
            log.error(f"SupervisorSyncEngine sync failed: {e}")
            
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
        return "SUPERVISOR"

    def is_available(self) -> bool:
        return self._supervisor_service is not None
