from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

class RouteOptimizer:
    def __init__(self) -> None:
        pass

    def optimize_evacuation_routes(
        self, workers_by_zone: dict[str, list[str]], safe_zones: list[str], 
        zone_graph: dict[str, list[str]], hazard_intensities: dict[str, float]
    ) -> dict:
        result = {}
        
        for z, workers in workers_by_zone.items():
            if not workers:
                continue
                
            best_target = None
            best_path = None
            min_cost = 999999
            
            for target in safe_zones:
                queue = [[z]]
                visited = set([z])
                found_path = None
                
                while queue:
                    path = queue.pop(0)
                    curr = path[-1]
                    if curr == target:
                        found_path = path
                        break
                    for nxt in zone_graph.get(curr, []):
                        if nxt not in visited and hazard_intensities.get(nxt, 0.0) <= 0.7:
                            visited.add(nxt)
                            queue.append(path + [nxt])
                            
                if found_path:
                    cost = sum(hazard_intensities.get(n, 0.0) for n in found_path) + len(found_path)*0.1
                    if cost < min_cost:
                        min_cost = cost
                        best_path = found_path
                        best_target = target
                        
            if best_path:
                result[z] = {
                    "route": best_path,
                    "worker_ids": workers,
                    "eta_minutes": len(best_path) * 2.0,
                    "assembly_point": best_target
                }
                
        return result

    def handle_route_conflict(self, routes: list[dict]) -> list[dict]:
        res = []
        used_bottlenecks = {}
        
        for r in routes:
            new_r = dict(r)
            path = new_r.get("route", [])
            delay = 0.0
            
            for node in path[1:-1]:
                if node in used_bottlenecks:
                    prev_count = used_bottlenecks[node]
                    delay = max(delay, prev_count * 0.5)
                    used_bottlenecks[node] += len(new_r.get("worker_ids", []))
                else:
                    used_bottlenecks[node] = len(new_r.get("worker_ids", []))
                    
            if delay > 0:
                new_r["eta_minutes"] = new_r.get("eta_minutes", 0.0) + delay
                
            res.append(new_r)
        return res

    def compute_crowd_density(self, worker_count: int, path_nodes: list[str], corridor_width_m: float = 2.0) -> float:
        area = max(1.0, len(path_nodes) * corridor_width_m * 2.0)
        return float(worker_count / area)

    def adjust_speed_for_crowd(self, base_speed_ms: float, crowd_density: float) -> float:
        return float(base_speed_ms * max(0.3, 1.0 - crowd_density * 0.5))

    def generate_dynamic_routing_update(self, current_routes: dict, new_hazard_intensities: dict[str, float]) -> dict:
        updates = {}
        for z, r in current_routes.items():
            path = r.get("route", [])
            if any(new_hazard_intensities.get(n, 0.0) > 0.5 for n in path):
                updates[z] = {"needs_reroute": True, "reason": "Hazard intensity increased on current path"}
            else:
                updates[z] = {"needs_reroute": False}
        return updates
