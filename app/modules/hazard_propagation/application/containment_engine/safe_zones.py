from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

class SafeZoneIdentifier:
    def __init__(self) -> None:
        pass

    def identify_safe_zones(self, all_zone_ids: list[str], exposure_scores: dict[str, float], safe_threshold: float = 0.1) -> list[str]:
        return [z for z in all_zone_ids if exposure_scores.get(z, 0.0) < safe_threshold]

    def find_nearest_safe_zone(self, source_zone_id: str, safe_zones: list[str], zone_distances: dict) -> str | None:
        if not safe_zones:
            return None
        
        def dist(sz):
            d = zone_distances.get((source_zone_id, sz))
            if d is None:
                d = zone_distances.get(sz, 999999.0)
            return d
            
        return min(safe_zones, key=dist)

    def compute_zone_safety_score(self, zone_id: str, exposure_score: float, ventilation_rate: float, barrier_count: int) -> float:
        score = (1.0 - exposure_score) * 0.5 + (ventilation_rate / 10.0) * 0.3 + (barrier_count / 5.0) * 0.2
        return max(0.0, min(1.0, float(score)))

    def rank_safe_zones(self, safe_zones: list[str], safety_scores: dict[str, float], capacity: dict[str, int]) -> list[dict]:
        ranked = []
        for z in safe_zones:
            ranked.append({
                "zone_id": z,
                "score": safety_scores.get(z, 0.0),
                "capacity": capacity.get(z, 50),
                "distance": 0.0
            })
        return sorted(ranked, key=lambda x: x["score"], reverse=True)

    def verify_evacuation_path_to_safe_zone(self, source: str, safe_zone: str, blocked_nodes: list[str], adjacency: dict[str, list[str]]) -> bool:
        if source == safe_zone:
            return True
        visited = set([source])
        queue = [source]
        while queue:
            curr = queue.pop(0)
            if curr == safe_zone:
                return True
            for nxt in adjacency.get(curr, []):
                if nxt not in visited and nxt not in blocked_nodes:
                    visited.add(nxt)
                    queue.append(nxt)
        return False

    def generate_assembly_points(self, safe_zones: list[str], zone_capacities: dict[str, int]) -> list[dict]:
        pts = []
        for i, z in enumerate(safe_zones):
            pts.append({
                "point_id": f"AP-{z}",
                "zone_id": z,
                "location": f"Assembly point in {z}",
                "capacity": zone_capacities.get(z, 50),
                "is_primary": (i == 0)
            })
        return pts
