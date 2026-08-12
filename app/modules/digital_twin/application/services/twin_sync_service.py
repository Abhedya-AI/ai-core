from __future__ import annotations

import time
import asyncio
from typing import Any, List, Dict
from app.core.logging import get_logger

log = get_logger(__name__)


class BaseSyncEngine:
    name = "base"
    async def sync(self, twin_id: str, context: dict) -> dict:
        return {"status": "SUCCESS", "updates": 1}

class SensorSyncEngine(BaseSyncEngine): name = "sensor"
class VisionSyncEngine(BaseSyncEngine): name = "vision"
class KGSyncEngine(BaseSyncEngine): name = "kg"
class RiskSyncEngine(BaseSyncEngine): name = "risk"
class ForecastSyncEngine(BaseSyncEngine): name = "forecast"
class HazardSyncEngine(BaseSyncEngine): name = "hazard"
class RCASyncEngine(BaseSyncEngine): name = "rca"
class SupervisorSyncEngine(BaseSyncEngine): name = "supervisor"


class TwinSyncService:
    def __init__(self, graphrag_service: Any = None) -> None:
        self.graphrag_service = graphrag_service
        self._engines: Dict[str, BaseSyncEngine] = {}
        
        engine_classes = [
            SensorSyncEngine, VisionSyncEngine, KGSyncEngine, RiskSyncEngine,
            ForecastSyncEngine, HazardSyncEngine, RCASyncEngine, SupervisorSyncEngine
        ]
        
        for cls in engine_classes:
            try:
                engine = cls()
                self._engines[engine.name] = engine
            except Exception as e:
                log.warning(f"Failed to initialize sync engine {cls.__name__}: {e}")

    async def sync_all(self, twin_id: str, context: dict[str, Any] = None) -> dict[str, Any]:
        t0 = time.perf_counter()
        context = context or {}
        results = {}
        total_updates = 0
        failed_sources = []
        
        try:
            tasks = [engine.sync(twin_id, context) for engine in self._engines.values()]
            engine_names = list(self._engines.keys())
            
            sync_responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for name, response in zip(engine_names, sync_responses):
                if isinstance(response, Exception):
                    failed_sources.append(name)
                    results[name] = {"status": "FAILED", "error": str(response)}
                else:
                    results[name] = response
                    total_updates += response.get("updates", 0)
                    if response.get("status") != "SUCCESS":
                        failed_sources.append(name)
                        
            return {
                "sources": results,
                "total_updates": total_updates,
                "failed_sources": failed_sources,
                "latency_ms": (time.perf_counter() - t0) * 1000
            }
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinSyncService.sync_all completed in {latency_ms:.2f}ms")

    async def sync_source(self, twin_id: str, source_name: str, context: dict[str, Any] = None) -> dict[str, Any]:
        t0 = time.perf_counter()
        context = context or {}
        try:
            if source_name not in self._engines:
                return {"status": "FAILED", "error": f"Source {source_name} not found"}
            result = await self._engines[source_name].sync(twin_id, context)
            return result
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinSyncService.sync_source completed in {latency_ms:.2f}ms")

    async def sync_incremental(self, twin_id: str, source_name: str, since: float, context: dict[str, Any] = None) -> dict[str, Any]:
        t0 = time.perf_counter()
        context = context or {}
        context["since"] = since
        try:
            return await self.sync_source(twin_id, source_name, context)
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinSyncService.sync_incremental completed in {latency_ms:.2f}ms")

    def get_sync_statuses(self) -> List[dict[str, Any]]:
        t0 = time.perf_counter()
        statuses = [{"source_name": name, "status": "AVAILABLE"} for name in self._engines.keys()]
        latency_ms = (time.perf_counter() - t0) * 1000
        log.info(f"get_sync_statuses completed in {latency_ms:.2f}ms")
        return statuses

    def is_source_available(self, source_name: str) -> bool:
        return source_name in self._engines
