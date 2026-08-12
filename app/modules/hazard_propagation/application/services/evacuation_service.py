from __future__ import annotations
import asyncio
import time
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class EvacuationService:
    def __init__(self) -> None:
        self._engines = None
        self._init_engines()

    def _init_engines(self) -> None:
        try:
            from app.modules.hazard_propagation.application.evacuation_engine.pathfinder import SafePathfinder
            from app.modules.hazard_propagation.application.evacuation_engine.route_optimizer import RouteOptimizer
            from app.modules.hazard_propagation.application.evacuation_engine.worker_prioritization import WorkerPrioritization
            from app.modules.hazard_propagation.application.evacuation_engine.assembly_points import AssemblyPointManager
            self._engines = {
                "pathfinder": SafePathfinder(),
                "optimizer": RouteOptimizer(),
                "priority": WorkerPrioritization(),
                "assembly": AssemblyPointManager()
            }
        except ImportError as e:
            log.warning(f"Evacuation engines not available: {e}")

    async def generate(self, propagation_id: str, zone_ids: list[str], worker_ids: list[str], hazard_intensities: dict[str, float], context: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        paths = {}
        routes = {}
        priorities = []
        assembly_points = []
        
        if self._engines:
            try:
                paths = await self._engines["pathfinder"].find_safe_paths(zone_ids, hazard_intensities)
                routes = await self._engines["optimizer"].optimize_routes(paths, worker_ids)
                priorities = await self._engines["priority"].prioritize(worker_ids, zone_ids, hazard_intensities)
                assembly_points = await self._engines["assembly"].generate(zone_ids, routes)
            except Exception as e:
                log.warning(f"Error generating evacuation plan: {e}")

        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "propagation_id": propagation_id,
            "recommendation_id": f"evac_{propagation_id}",
            "paths": paths,
            "routes": routes,
            "priorities": priorities,
            "assembly_points": assembly_points,
            "latency_ms": latency_ms
        }
