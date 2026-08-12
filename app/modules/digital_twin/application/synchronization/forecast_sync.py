from __future__ import annotations
from typing import Any
import time
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.digital_twin.application.synchronization.base import AbstractSyncEngine, SyncResult, SyncConflictResolver

log = get_logger(__name__)

class ForecastSyncEngine(AbstractSyncEngine):
    def __init__(self):
        try:
            from app.modules.forecast.application.services.forecast_orchestration_service import ForecastOrchestrationService
            self._forecast_service = ForecastOrchestrationService()
        except ImportError:
            self._forecast_service = None
            log.warning("ForecastOrchestrationService not available. Falling back to context data.")
        self._resolver = SyncConflictResolver()

    async def sync(self, twin_id: str, context: dict[str, Any]) -> SyncResult:
        t0 = time.perf_counter()
        entity_updates: dict[str, Any] = {}
        error_message = None
        status = "COMPLETED"
        
        try:
            entity_ids = context.get("entity_ids", [])
            if self._forecast_service and hasattr(self._forecast_service, "get_forecasts"):
                for entity_id in entity_ids:
                    f_data = await self._forecast_service.get_forecasts(entity_id)
                    if f_data:
                        entity_updates[entity_id] = {
                            "predicted_health": f_data.get("predicted_health", 1.0),
                            "rul_hours": f_data.get("rul_hours", -1),
                            "failure_probability": f_data.get("failure_probability", 0.0),
                            "trend": f_data.get("trend", "STABLE")
                        }
                        
            context_data = context.get("forecast_data", {})
            for entity_id, data in context_data.items():
                existing = entity_updates.get(entity_id, {})
                entity_updates[entity_id] = self._resolver.resolve(existing, data, self.get_source())
                
        except Exception as e:
            error_message = str(e)
            status = "FAILED"
            log.error(f"ForecastSyncEngine sync failed: {e}")
            
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
        return "FORECAST"

    def is_available(self) -> bool:
        return self._forecast_service is not None
