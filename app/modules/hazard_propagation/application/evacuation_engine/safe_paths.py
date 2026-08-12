from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

class SafePathFinder:
    def __init__(self, path_optimizer=None) -> None:
        self.path_optimizer = path_optimizer

    async def find_safe_paths(self, source_zone: str, safe_zones: list[str], zone_graph: dict[str, list[str]], hazard_intensities: dict[str, float], blocked_nodes: list[str] | None = None) -> list[dict]:
        blocks = set(blocked_nodes or [])
        paths = []
        
        for idx, target in enumerate(safe_zones):
            queue = [[source_zone]]
            visited = set([source_zone])
            found_path = None
            
            while queue:
                path = queue.pop(0)
                curr = path[-1]
                
                if curr == target:
                    found_path = path
                    break
                    
                for nxt in zone_graph.get(curr, []):
                    if nxt not in visited and nxt not in blocks:
                        if hazard_intensities.get(nxt, 0.0) <= 0.7:
                            visited.add(nxt)
                            queue.append(path + [nxt])
                            
            if found_path:
                exp_score = sum(hazard_intensities.get(n, 0.0) for n in found_path) / len(found_path)
                eta = len(found_path) * 2.0 
                paths.append({
                    "path": found_path,
                    "exposure_score": exp_score,
                    "eta_minutes": eta,
                    "is_primary": False
                })
                
        if paths:
            paths.sort(key=lambda x: x["exposure_score"])
            paths[0]["is_primary"] = True
            
        return paths

    def find_alternative_routes(self, primary_path: list[str], zone_graph: dict[str, list[str]], hazard_intensities: dict[str, float]) -> list[list[str]]:
        if not primary_path:
            return []
            
        source = primary_path[0]
        target = primary_path[-1]
        blocks = set(primary_path[1:-1])
        
        queue = [[source]]
        visited = set([source])
        alts = []
        
        while queue:
            path = queue.pop(0)
            curr = path[-1]
            
            if curr == target:
                if path != primary_path:
                    alts.append(path)
                continue
                
            for nxt in zone_graph.get(curr, []):
                if nxt not in visited and nxt not in blocks:
                    if hazard_intensities.get(nxt, 0.0) <= 0.7:
                        visited.add(nxt)
                        queue.append(path + [nxt])
                        
        return alts

    def check_all_routes_blocked(self, source: str, safe_zones: list[str], blocked_nodes: list[str], adjacency: dict[str, list[str]]) -> bool:
        blocks = set(blocked_nodes or [])
        
        for sz in safe_zones:
            queue = [source]
            visited = set([source])
            found = False
            
            while queue:
                curr = queue.pop(0)
                if curr == sz:
                    found = True
                    break
                for nxt in adjacency.get(curr, []):
                    if nxt not in visited and nxt not in blocks:
                        visited.add(nxt)
                        queue.append(nxt)
            if found:
                return False
                
        return True

    def rank_exit_routes(self, paths: list[dict]) -> list[dict]:
        return sorted(paths, key=lambda x: x.get("exposure_score", 99.0))

    def compute_path_safety_margin(self, path: list[str], hazard_intensities: dict[str, float], safety_threshold: float = 0.3) -> float:
        if not path:
            return 0.0
        margins = [max(0.0, safety_threshold - hazard_intensities.get(n, 0.0)) for n in path]
        return sum(margins) / len(margins)
