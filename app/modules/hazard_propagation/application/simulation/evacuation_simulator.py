from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

class EvacuationSimulator:
    def __init__(self) -> None:
        pass

    async def simulate_evacuation(self, workers_by_zone: dict[str, int], routes: dict[str, list[str]], hazard_spread_timeline: list[dict], time_horizon_minutes: int = 30) -> dict:
        total_workers = sum(workers_by_zone.values())
        safely_evacuated = 0
        blocked_routes = 0
        total_time = 0.0
        
        for z, count in workers_by_zone.items():
            route = routes.get(z, [])
            block_time = self.simulate_route_blocking(route, hazard_spread_timeline)
            
            evac_time = len(route) * 2.0
            
            if block_time is not None and block_time < evac_time:
                safely_evacuated += int(count * (block_time / evac_time))
                blocked_routes += 1
                total_time = max(total_time, block_time)
            else:
                safely_evacuated += count
                total_time = max(total_time, evac_time)
                
        rate = safely_evacuated / max(1, total_workers)
        
        return {
            "evacuation_success_rate": float(rate),
            "workers_evacuated_safely": safely_evacuated,
            "workers_at_risk": total_workers - safely_evacuated,
            "routes_blocked_mid_evacuation": blocked_routes,
            "estimated_completion_time": float(total_time)
        }

    def simulate_route_blocking(self, route: list[str], hazard_timeline: list[dict], hazard_threshold: float = 0.5) -> float | None:
        for t_idx, state in enumerate(hazard_timeline):
            for n in route:
                if state.get(n, 0.0) > hazard_threshold:
                    return float(t_idx)
        return None

    def compute_evacuation_success_probability(self, worker_count: int, available_time_minutes: float, evacuation_time_minutes: float) -> float:
        prob = (available_time_minutes / max(0.01, evacuation_time_minutes)) * 0.9
        return max(0.0, min(1.0, float(prob)))

    def simulate_staged_evacuation(self, worker_groups: list[list[dict]], routes: list[dict]) -> dict:
        stages = []
        tot_time = 0.0
        for i, grp in enumerate(worker_groups):
            route = routes[i % len(routes)]
            eta = route.get("eta_minutes", 5.0) + (i * 2.0) 
            stages.append({
                "group_index": i,
                "worker_count": len(grp),
                "route": route.get("path", []),
                "eta_minutes": eta
            })
            tot_time = max(tot_time, eta)
            
        return {
            "stages": stages,
            "total_time": tot_time
        }
