from __future__ import annotations

import time
from datetime import datetime, timezone

import numpy as np

from app.core.logging import get_logger

try:
    from app.modules.platform.plants.plant_registry import PlantRegistry, get_service as get_registry
except ImportError:
    PlantRegistry = Any
    get_registry = lambda: None

log = get_logger(__name__)

class FleetHealthMonitor:
    def __init__(self, plant_registry: PlantRegistry | None = None) -> None:
        self.plant_registry = plant_registry or get_registry()

    async def get_fleet_health(self, tenant_id: str | None = None) -> dict:
        start_time = time.perf_counter()
        try:
            if tenant_id:
                plants = await self.plant_registry.list(tenant_id, limit=1000)
            else:
                plants = [p for p in await self.plant_registry.get_all_active()]
                
            if not plants:
                return {
                    "total_plants": 0,
                    "active_plants": 0,
                    "maintenance_plants": 0,
                    "offline_plants": 0,
                    "fleet_oee": 0.0,
                    "fleet_safety_index": 0.0,
                    "total_equipment": 0,
                    "total_workers": 0,
                    "plants": [],
                    "health_score": 0.0,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }

            active_plants = [p for p in plants if p.status == "ACTIVE"]
            maintenance_plants = [p for p in plants if p.status == "MAINTENANCE"]
            offline_plants = [p for p in plants if p.status == "OFFLINE"]

            oee_scores = np.array([p.oee_score for p in plants])
            safety_indices = np.array([p.safety_index for p in plants])

            mean_oee = float(np.mean(oee_scores))
            mean_safety = float(np.mean(safety_indices))
            
            active_ratio = len(active_plants) / len(plants)
            
            health_score = 0.4 * mean_oee + 0.4 * mean_safety + 0.2 * active_ratio

            plant_summaries = []
            for p in plants:
                hl = "HEALTHY"
                if p.oee_score < 0.6 or p.safety_index < 0.8:
                    hl = "DEGRADED"
                if p.oee_score < 0.4 or p.safety_index < 0.6 or p.status == "OFFLINE":
                    hl = "CRITICAL"
                    
                plant_summaries.append({
                    "plant_id": p.plant_id,
                    "name": p.name,
                    "status": p.status,
                    "oee_score": p.oee_score,
                    "safety_index": p.safety_index,
                    "health_level": hl
                })

            return {
                "total_plants": len(plants),
                "active_plants": len(active_plants),
                "maintenance_plants": len(maintenance_plants),
                "offline_plants": len(offline_plants),
                "fleet_oee": mean_oee,
                "fleet_safety_index": mean_safety,
                "total_equipment": sum(p.equipment_count for p in plants),
                "total_workers": sum(p.worker_count for p in plants),
                "plants": plant_summaries,
                "health_score": health_score,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_fleet_health executed in {latency:.4f}s")

    async def get_plant_health(self, plant_id: str) -> dict:
        start_time = time.perf_counter()
        try:
            plant = await self.plant_registry.get(plant_id)
            if not plant:
                raise ValueError("Plant not found")
                
            hl = "HEALTHY"
            if plant.oee_score < 0.6 or plant.safety_index < 0.8:
                hl = "DEGRADED"
            if plant.oee_score < 0.4 or plant.safety_index < 0.6 or plant.status == "OFFLINE":
                hl = "CRITICAL"
                
            return {
                "plant_id": plant.plant_id,
                "status": plant.status,
                "oee_score": plant.oee_score,
                "safety_index": plant.safety_index,
                "equipment_count": plant.equipment_count,
                "worker_count": plant.worker_count,
                "health_level": hl
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_plant_health executed in {latency:.4f}s")

    async def get_fleet_trend(self, tenant_id: str, window_hours: int = 24) -> dict:
        start_time = time.perf_counter()
        try:
            # Placeholder for historical data aggregation
            return {
                "trend_direction": "STABLE",
                "oee_trend": 0.0,
                "safety_trend": 0.0,
                "fleet_health_history": []
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_fleet_trend executed in {latency:.4f}s")

    async def alert_unhealthy_plants(self, threshold: float = 0.5) -> list[dict]:
        start_time = time.perf_counter()
        try:
            health_report = await self.get_fleet_health()
            unhealthy = []
            for p in health_report["plants"]:
                score = 0.5 * p["oee_score"] + 0.5 * p["safety_index"]
                if score < threshold:
                    unhealthy.append(p)
            return unhealthy
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"alert_unhealthy_plants executed in {latency:.4f}s")

_service_instance = None
def get_service() -> FleetHealthMonitor:
    global _service_instance
    if _service_instance is None:
        _service_instance = FleetHealthMonitor()
    return _service_instance
