from __future__ import annotations
import networkx as nx
from app.core.logging import get_logger

log = get_logger(__name__)

class EvacuationPathOptimizer:
    """Optimizer for safe evacuation paths."""

    def __init__(self) -> None:
        pass

    def find_safe_evacuation_path(self, graph: nx.DiGraph, start_node: str, safe_nodes: list[str], hazard_intensities: dict[str, float]) -> list[str] | None:
        """Find safest path to any safe node."""
        if start_node not in graph:
            return None
            
        def weight_func(u, v, d):
            # Cost is hazard intensity + small base cost
            intensity = hazard_intensities.get(v, 0.0)
            if intensity > 0.7:
                return float('inf')
            return intensity + 0.1

        best_path = None
        best_cost = float('inf')
        
        for safe_node in safe_nodes:
            if safe_node not in graph:
                continue
            try:
                path = nx.shortest_path(graph, start_node, safe_node, weight=weight_func)
                cost = sum(hazard_intensities.get(n, 0.0) for n in path)
                if cost < best_cost:
                    best_cost = cost
                    best_path = path
            except nx.NetworkXNoPath:
                continue
                
        return best_path

    def rank_paths_by_safety(self, paths: list[list[str]], hazard_intensities: dict[str, float]) -> list[tuple[list[str], float]]:
        """Rank paths by total hazard exposure."""
        ranked = []
        for p in paths:
            exposure = self.compute_path_exposure(p, hazard_intensities)
            ranked.append((p, exposure))
        return sorted(ranked, key=lambda x: x[1])

    def compute_path_exposure(self, path: list[str], hazard_intensities: dict[str, float]) -> float:
        """Sum of intensities along path."""
        return sum(hazard_intensities.get(n, 0.0) for n in path)

    def find_multiple_safe_paths(self, graph: nx.DiGraph, start: str, safe_nodes: list[str], intensities: dict[str, float], max_paths: int = 3) -> list[list[str]]:
        """Find multiple safe paths."""
        paths = []
        if start not in graph:
            return paths
            
        for safe_node in safe_nodes:
            if safe_node not in graph:
                continue
            try:
                # Using simple paths might be slow, just find shortest path for now
                path = self.find_safe_evacuation_path(graph, start, [safe_node], intensities)
                if path and path not in paths:
                    paths.append(path)
            except Exception:
                pass
                
        return paths[:max_paths]

    def compute_evacuation_eta(self, path: list[str], distances: dict[tuple, float], walking_speed_ms: float = 1.2) -> float:
        """Estimate evacuation time in minutes."""
        if not path or len(path) < 2:
            return 0.0
            
        total_dist = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            dist = distances.get((u, v), distances.get((v, u), 10.0))
            total_dist += dist
            
        time_s = total_dist / max(0.1, walking_speed_ms)
        return time_s / 60.0

    def check_path_blocked(self, path: list[str], blocked_nodes: set[str]) -> bool:
        """Check if path is blocked."""
        return any(node in blocked_nodes for node in path)
