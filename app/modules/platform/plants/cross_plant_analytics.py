from __future__ import annotations

import time
import numpy as np
from typing import Any

from app.core.logging import get_logger

try:
    from app.modules.platform.plants.plant_registry import PlantRegistry, get_service as get_registry
except ImportError:
    PlantRegistry = Any
    get_registry = lambda: None

log = get_logger(__name__)

class CrossPlantAnalytics:
    def __init__(self, plant_registry: PlantRegistry | None = None) -> None:
        self.plant_registry = plant_registry or get_registry()

    async def rank_plants(self, tenant_id: str, metric: str = "oee_score") -> list[dict]:
        start_time = time.perf_counter()
        try:
            plants = await self.plant_registry.list(tenant_id, limit=1000)
            if not plants:
                return []
                
            values = np.array([getattr(p, metric, 0.0) for p in plants])
            sorted_indices = np.argsort(-values)
            
            ranks = []
            for i, idx in enumerate(sorted_indices):
                plant = plants[idx]
                val = values[idx]
                # Avoid division by zero
                percentile = 100.0 if len(plants) <= 1 else float(np.percentile(values, ((len(plants) - i - 1) / (len(plants) - 1)) * 100))
                
                ranks.append({
                    "rank": i + 1,
                    "plant_id": plant.plant_id,
                    "name": plant.name,
                    "metric_value": float(val),
                    "percentile": percentile
                })
                
            return ranks
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"rank_plants executed in {latency:.4f}s")

    async def benchmark(self, plant_id: str, tenant_id: str) -> dict:
        start_time = time.perf_counter()
        try:
            target = await self.plant_registry.get(plant_id)
            if not target:
                raise ValueError("Plant not found")
                
            plants = await self.plant_registry.list(tenant_id, limit=1000)
            
            oee_arr = np.array([p.oee_score for p in plants])
            safety_arr = np.array([p.safety_index for p in plants])
            
            fleet_avg = {
                "oee_score": float(np.mean(oee_arr)),
                "safety_index": float(np.mean(safety_arr))
            }
            
            fleet_best = {
                "oee_score": float(np.max(oee_arr)),
                "safety_index": float(np.max(safety_arr))
            }
            
            gaps = {
                "oee_score": fleet_best["oee_score"] - target.oee_score,
                "safety_index": fleet_best["safety_index"] - target.safety_index
            }
            
            percentile_rank = float(np.sum(oee_arr <= target.oee_score) / len(oee_arr)) * 100
            
            return {
                "plant_id": plant_id,
                "plant_metrics": {
                    "oee_score": target.oee_score,
                    "safety_index": target.safety_index
                },
                "fleet_average": fleet_avg,
                "fleet_best": fleet_best,
                "gaps": gaps,
                "percentile_rank": percentile_rank
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"benchmark executed in {latency:.4f}s")

    async def correlate(self, metric_a: str, metric_b: str, tenant_id: str) -> dict:
        start_time = time.perf_counter()
        try:
            plants = await self.plant_registry.list(tenant_id, limit=1000)
            if len(plants) < 2:
                return {"correlation": 0.0, "interpretation": "Insufficient data", "plant_count": len(plants)}
                
            arr_a = np.array([getattr(p, metric_a, 0.0) for p in plants])
            arr_b = np.array([getattr(p, metric_b, 0.0) for p in plants])
            
            corr_matrix = np.corrcoef(arr_a, arr_b)
            corr = float(corr_matrix[0, 1]) if not np.isnan(corr_matrix[0, 1]) else 0.0
            
            interpretation = "None"
            if abs(corr) > 0.7:
                interpretation = "Strong"
            elif abs(corr) > 0.3:
                interpretation = "Moderate"
            else:
                interpretation = "Weak"
                
            if corr < 0 and interpretation != "None":
                interpretation += " Negative"
            elif corr > 0 and interpretation != "None":
                interpretation += " Positive"
                
            return {
                "correlation": corr,
                "interpretation": interpretation,
                "plant_count": len(plants)
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"correlate executed in {latency:.4f}s")

    async def find_similar_plants(self, plant_id: str, top_k: int = 3) -> list[dict]:
        start_time = time.perf_counter()
        try:
            target = await self.plant_registry.get(plant_id)
            if not target:
                raise ValueError("Plant not found")
                
            plants = await self.plant_registry.list(target.tenant_id, limit=1000)
            
            target_vec = np.array([target.oee_score, target.safety_index])
            
            distances = []
            for p in plants:
                if p.plant_id == plant_id:
                    continue
                p_vec = np.array([p.oee_score, p.safety_index])
                dist = np.linalg.norm(target_vec - p_vec)
                distances.append((dist, p))
                
            distances.sort(key=lambda x: x[0])
            
            results = []
            for dist, p in distances[:top_k]:
                results.append({
                    "plant_id": p.plant_id,
                    "name": p.name,
                    "distance": float(dist),
                    "oee_score": p.oee_score,
                    "safety_index": p.safety_index
                })
                
            return results
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"find_similar_plants executed in {latency:.4f}s")

    async def compute_fleet_kpis(self, tenant_id: str) -> dict:
        start_time = time.perf_counter()
        try:
            plants = await self.plant_registry.list(tenant_id, limit=1000)
            if not plants:
                return {}
                
            oee_arr = np.array([p.oee_score for p in plants])
            safety_arr = np.array([p.safety_index for p in plants])
            
            best_oee_idx = np.argmax(oee_arr)
            worst_oee_idx = np.argmin(oee_arr)
            
            return {
                "avg_oee": float(np.mean(oee_arr)),
                "avg_safety_index": float(np.mean(safety_arr)),
                "best_oee_plant": plants[best_oee_idx].plant_id,
                "worst_oee_plant": plants[worst_oee_idx].plant_id,
                "oee_std": float(np.std(oee_arr)),
                "safety_std": float(np.std(safety_arr)),
                "fleet_size": len(plants)
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"compute_fleet_kpis executed in {latency:.4f}s")

_service_instance = None
def get_service() -> CrossPlantAnalytics:
    global _service_instance
    if _service_instance is None:
        _service_instance = CrossPlantAnalytics()
    return _service_instance
