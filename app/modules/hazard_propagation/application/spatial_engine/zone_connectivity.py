from __future__ import annotations
from collections import deque
from app.core.logging import get_logger

log = get_logger(__name__)

class ZoneConnectivityMapper:
    """Mapper for zone connectivity and adjacency."""

    def __init__(self, knowledge_service=None) -> None:
        self._knowledge_service = knowledge_service

    async def build_zone_adjacency(self, zone_ids: list[str]) -> dict[str, list[str]]:
        """Build adjacency mapping for zones."""
        if not zone_ids:
            return {}

        adjacency = {z: [] for z in zone_ids}
        
        # Default chain topology: each zone connects to next 2 in list
        for i, zone_id in enumerate(zone_ids):
            for j in range(1, 3):
                if i + j < len(zone_ids):
                    target = zone_ids[i + j]
                    adjacency[zone_id].append(target)
                    adjacency[target].append(zone_id)
                    
        # Remove duplicates
        for k in adjacency:
            adjacency[k] = list(set(adjacency[k]))
            
        return adjacency

    def compute_connectivity_score(self, zone_id: str, adjacency: dict[str, list[str]]) -> float:
        """Compute connectivity score based on neighbors."""
        if zone_id not in adjacency or len(adjacency) <= 1:
            return 0.0
        return len(adjacency[zone_id]) / max(1, len(adjacency) - 1)

    def find_isolated_zones(self, adjacency: dict[str, list[str]], connected_threshold: int = 2) -> list[str]:
        """Find zones with fewer than threshold connections."""
        return [z for z, neighbors in adjacency.items() if len(neighbors) < connected_threshold]

    def compute_path_between_zones(self, zone_a: str, zone_b: str, adjacency: dict[str, list[str]]) -> list[str] | None:
        """BFS to compute shortest path in terms of zones."""
        if zone_a not in adjacency or zone_b not in adjacency:
            return None
        if zone_a == zone_b:
            return [zone_a]
            
        queue = deque([[zone_a]])
        visited = {zone_a}
        
        while queue:
            path = queue.popleft()
            curr = path[-1]
            
            for neighbor in adjacency.get(curr, []):
                if neighbor == zone_b:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
                    
        return None

    def rank_zones_by_connectivity(self, adjacency: dict[str, list[str]]) -> list[tuple[str, int]]:
        """Rank zones by connection count descending."""
        counts = [(z, len(neighbors)) for z, neighbors in adjacency.items()]
        return sorted(counts, key=lambda x: x[1], reverse=True)
