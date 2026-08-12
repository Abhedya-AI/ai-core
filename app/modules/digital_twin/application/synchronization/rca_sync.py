from __future__ import annotations
from typing import Any
import time
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.digital_twin.application.synchronization.base import AbstractSyncEngine, SyncResult, SyncConflictResolver

log = get_logger(__name__)

class RCASyncEngine(AbstractSyncEngine):
    def __init__(self):
        try:
            from app.modules.root_cause.services.root_cause_service import RootCauseService
            self._rca_service = RootCauseService()
        except ImportError:
            self._rca_service = None
            log.warning("RootCauseService not available. Falling back to context data.")
        self._resolver = SyncConflictResolver()

    async def sync(self, twin_id: str, context: dict[str, Any]) -> SyncResult:
        t0 = time.perf_counter()
        entity_updates: dict[str, Any] = {}
        error_message = None
        status = "COMPLETED"
        
        try:
            if self._rca_service and hasattr(self._rca_service, "get_recent_findings"):
                findings = await self._rca_service.get_recent_findings(twin_id)
                for f in findings:
                    entity_id = f.get("entity_id")
                    if entity_id:
                        if entity_id not in entity_updates:
                            entity_updates[entity_id] = {
                                "rca_findings": [],
                                "causal_factors": [],
                                "recommendation": ""
                            }
                        entity_updates[entity_id]["rca_findings"].append(f.get("finding", ""))
                        entity_updates[entity_id]["causal_factors"].extend(f.get("causal_factors", []))
                        entity_updates[entity_id]["recommendation"] = f.get("recommendation", "")
                        
            context_data = context.get("rca_data", {})
            for entity_id, data in context_data.items():
                existing = entity_updates.get(entity_id, {})
                entity_updates[entity_id] = self._resolver.resolve(existing, data, self.get_source())
                
        except Exception as e:
            error_message = str(e)
            status = "FAILED"
            log.error(f"RCASyncEngine sync failed: {e}")
            
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
        return "ROOT_CAUSE"

    def is_available(self) -> bool:
        return self._rca_service is not None
