from __future__ import annotations
from typing import Any
import time
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.digital_twin.application.synchronization.base import AbstractSyncEngine, SyncResult, SyncConflictResolver

log = get_logger(__name__)

class RiskSyncEngine(AbstractSyncEngine):
    def __init__(self):
        try:
            from app.modules.risk_prediction.application.services.risk_orchestration_service import RiskOrchestrationService
            self._risk_service = RiskOrchestrationService()
        except ImportError:
            self._risk_service = None
            log.warning("RiskOrchestrationService not available. Falling back to context data.")
        self._resolver = SyncConflictResolver()

    async def sync(self, twin_id: str, context: dict[str, Any]) -> SyncResult:
        t0 = time.perf_counter()
        entity_updates: dict[str, Any] = {}
        error_message = None
        status = "COMPLETED"
        
        try:
            entity_ids = context.get("entity_ids", [])
            if self._risk_service and hasattr(self._risk_service, "get_risk_scores"):
                for entity_id in entity_ids:
                    risk_data = await self._risk_service.get_risk_scores(entity_id)
                    if risk_data:
                        entity_updates[entity_id] = {
                            "risk_score": risk_data.get("risk_score", 0.0),
                            "risk_level": risk_data.get("risk_level", "LOW"),
                            "risk_factors": risk_data.get("risk_factors", []),
                            "forecast_horizon": risk_data.get("forecast_horizon", "1h")
                        }
                        
            context_data = context.get("risk_data", {})
            for entity_id, data in context_data.items():
                existing = entity_updates.get(entity_id, {})
                entity_updates[entity_id] = self._resolver.resolve(existing, data, self.get_source())
                
        except Exception as e:
            error_message = str(e)
            status = "FAILED"
            log.error(f"RiskSyncEngine sync failed: {e}")
            
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
        return "RISK"

    def is_available(self) -> bool:
        return self._risk_service is not None
