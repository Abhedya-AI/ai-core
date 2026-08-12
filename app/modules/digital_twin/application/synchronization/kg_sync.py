from __future__ import annotations
from typing import Any
import time
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.digital_twin.application.synchronization.base import AbstractSyncEngine, SyncResult, SyncConflictResolver

log = get_logger(__name__)

class KnowledgeGraphSyncEngine(AbstractSyncEngine):
    def __init__(self):
        try:
            from app.modules.knowledge.services.knowledge_service import KnowledgeService
            self._kg_service = KnowledgeService()
        except ImportError:
            self._kg_service = None
            log.warning("KnowledgeService not available. Falling back to context data.")
        self._resolver = SyncConflictResolver()

    async def sync(self, twin_id: str, context: dict[str, Any]) -> SyncResult:
        t0 = time.perf_counter()
        entity_updates: dict[str, Any] = {}
        error_message = None
        status = "COMPLETED"
        
        try:
            if self._kg_service:
                # Mock implementation assuming these methods exist
                if hasattr(self._kg_service, "get_equipment_list"):
                    equipments = await self._kg_service.get_equipment_list(twin_id)
                    for eq in equipments:
                        eq_id = eq.get("id")
                        if eq_id:
                            entity_updates[eq_id] = eq

                if hasattr(self._kg_service, "get_zone_list"):
                    zones = await self._kg_service.get_zone_list(twin_id)
                    for z in zones:
                        z_id = z.get("id")
                        if z_id:
                            entity_updates[z_id] = z
                            
                if hasattr(self._kg_service, "get_worker_list"):
                    workers = await self._kg_service.get_worker_list(twin_id)
                    for w in workers:
                        w_id = w.get("id")
                        if w_id:
                            entity_updates[w_id] = w
                            
                if hasattr(self._kg_service, "get_pipeline_list"):
                    pipelines = await self._kg_service.get_pipeline_list(twin_id)
                    for p in pipelines:
                        p_id = p.get("id")
                        if p_id:
                            entity_updates[p_id] = p
                            
            context_data = context.get("kg_data", {})
            for entity_id, data in context_data.items():
                existing = entity_updates.get(entity_id, {})
                entity_updates[entity_id] = self._resolver.resolve(existing, data, self.get_source())
                
        except Exception as e:
            error_message = str(e)
            status = "FAILED"
            log.error(f"KnowledgeGraphSyncEngine sync failed: {e}")
            
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
        
    async def get_entity_neighbors(self, entity_id: str) -> list[dict]:
        if not self._kg_service or not hasattr(self._kg_service, "get_neighbors"):
            return []
        try:
            return await self._kg_service.get_neighbors(entity_id)
        except Exception as e:
            log.error(f"Failed to get entity neighbors for {entity_id}: {e}")
            return []

    def get_source(self) -> str:
        return "KNOWLEDGE_GRAPH"

    def is_available(self) -> bool:
        return self._kg_service is not None
