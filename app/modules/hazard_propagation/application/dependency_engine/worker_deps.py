from __future__ import annotations
from app.core.logging import get_logger

log = get_logger(__name__)

class WorkerDependencyAnalyzer:
    """Analyzes worker dependencies and exposures."""

    def __init__(self, knowledge_service=None) -> None:
        self._knowledge_service = knowledge_service

    async def analyze_worker_exposure(self, worker_ids: list[str], zone_exposures: dict[str, float]) -> list[dict]:
        """Analyze hazard exposure for workers."""
        analysis = []
        for wid in worker_ids:
            zone = "ZONE-UNKNOWN"
            exposure = zone_exposures.get(zone, 0.0)
            
            analysis.append({
                "worker_id": wid,
                "zone_id": zone,
                "exposure_score": exposure,
                "evacuation_priority": exposure * 10.0
            })
            
        return analysis

    def prioritize_evacuation(self, worker_analysis: list[dict]) -> list[dict]:
        """Rank workers by evacuation priority."""
        return sorted(worker_analysis, key=lambda x: x.get("evacuation_priority", 0.0), reverse=True)

    def compute_worker_vulnerability(self, worker_metadata: dict) -> float:
        """Compute vulnerability score for a worker."""
        ppe = worker_metadata.get("ppe_score", 0.5)
        prox = worker_metadata.get("proximity_score", 0.3)
        
        vuln = 0.3 + (1.0 - ppe) * 0.3 + prox * 0.4
        return max(0.0, min(1.0, vuln))

    def find_isolated_workers(self, worker_ids: list[str], zone_adjacency: dict[str, list[str]], hazard_zones: set[str]) -> list[str]:
        """Find workers trapped by hazard zones."""
        isolated = []
        for wid in worker_ids:
            zone = "ZONE-UNKNOWN" # Without real mapping, assume default
            
            if zone in zone_adjacency:
                neighbors = zone_adjacency[zone]
                if all(n in hazard_zones for n in neighbors):
                    isolated.append(wid)
                    
        return isolated

    def estimate_evacuation_time(self, worker_count: int, path_length_meters: float, egress_width_meters: float = 2.0) -> float:
        """Estimate time to evacuate in minutes."""
        t_walk = path_length_meters / (1.2 * 60.0)
        t_queue = worker_count / max(0.1, egress_width_meters * 1.5)
        return max(t_walk, t_queue)
