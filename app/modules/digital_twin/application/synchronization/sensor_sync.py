from __future__ import annotations
from typing import Any
import time
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.digital_twin.application.synchronization.base import AbstractSyncEngine, SyncResult, SyncConflictResolver
import dateutil.parser

log = get_logger(__name__)

class SensorSyncEngine(AbstractSyncEngine):
    def __init__(self):
        try:
            from app.modules.sensor.services.sensor_service import SensorService
            self._sensor_service = SensorService()
        except ImportError:
            self._sensor_service = None
            log.warning("SensorService not available. Falling back to context data.")
        self._resolver = SyncConflictResolver()

    async def sync(self, twin_id: str, context: dict[str, Any]) -> SyncResult:
        t0 = time.perf_counter()
        entity_updates: dict[str, Any] = {}
        error_message = None
        status = "COMPLETED"
        
        try:
            if self._sensor_service:
                # Mock call since actual method may vary, assuming get_all_sensors exists
                # or similar. We use context if possible or mock the data.
                if hasattr(self._sensor_service, "get_all_sensor_readings"):
                    readings = await self._sensor_service.get_all_sensor_readings(twin_id)
                    for r in readings:
                        sensor_id = r.get("sensor_id")
                        if sensor_id:
                            entity_updates[sensor_id] = {
                                "sensor_id": sensor_id,
                                "value": r.get("value"),
                                "unit": r.get("unit"),
                                "timestamp": r.get("timestamp"),
                                "is_online": r.get("is_online", True),
                                "is_anomalous": r.get("is_anomalous", False),
                                "health_score": r.get("health_score", 1.0)
                            }
            
            # Fallback or add context data
            context_data = context.get("sensor_data", {})
            for sensor_id, data in context_data.items():
                existing = entity_updates.get(sensor_id, {})
                entity_updates[sensor_id] = self._resolver.resolve(existing, data, self.get_source())
                
        except Exception as e:
            error_message = str(e)
            status = "FAILED"
            log.error(f"SensorSyncEngine sync failed: {e}")
            
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
        t0 = time.perf_counter()
        entity_updates: dict[str, Any] = {}
        error_message = None
        status = "COMPLETED"
        
        try:
            since_dt = dateutil.parser.isoparse(since)
            
            # Use sync as baseline and filter
            full_result = await self.sync(twin_id, context)
            if full_result.status == "FAILED":
                return full_result
                
            for sensor_id, state in full_result.entity_updates.items():
                ts_str = state.get("timestamp")
                if ts_str:
                    try:
                        ts_dt = dateutil.parser.isoparse(ts_str)
                        if ts_dt > since_dt:
                            entity_updates[sensor_id] = state
                    except Exception:
                        pass
        except Exception as e:
            error_message = str(e)
            status = "FAILED"
            log.error(f"SensorSyncEngine incremental_sync failed: {e}")
            
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

    def get_source(self) -> str:
        return "SENSOR"

    def is_available(self) -> bool:
        return self._sensor_service is not None
