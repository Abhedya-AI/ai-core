from __future__ import annotations
from typing import Any
from app.core.logging import get_logger
from app.modules.hazard_propagation.application.propagation_models.base import PropagationResult

log = get_logger(__name__)

class EquipmentFailurePropagationModel:
    """Dependency failure model for equipment."""
    
    def __init__(self, base_p_fail: float = 0.1) -> None:
        self.base_p_fail = base_p_fail

    async def propagate(
        self,
        source_node_id: str,
        initial_intensity: float,
        graph_nodes: list[dict],
        graph_edges: list[dict],
        context: dict[str, Any],
        time_steps: int,
    ) -> PropagationResult:
        log.debug(f"EquipmentFailurePropagationModel.propagate: source={source_node_id}")
        
        if not graph_nodes:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
            
        node_ids = [n["node_id"] for n in graph_nodes]
        failed_nodes = set()
        
        if initial_intensity > 0.5:
            failed_nodes.add(source_node_id)
            
        adj: dict[str, list[tuple[str, float]]] = {nid: [] for nid in node_ids}
        for edge in graph_edges:
            src = edge.get("source_node_id", "")
            tgt = edge.get("target_node_id", "")
            dep_str = float(edge.get("metadata", {}).get("weight", 0.3))
            if src in adj: adj[src].append((tgt, dep_str))
            
        arrival_times = {source_node_id: 0.0} if source_node_id in failed_nodes else {}
        dt = 1.0
        
        for step in range(time_steps):
            new_failures = set()
            t_current = step * dt
            
            for failed_node in failed_nodes:
                for neighbor_id, dep_str in adj.get(failed_node, []):
                    if neighbor_id not in failed_nodes and neighbor_id not in new_failures:
                        p_fail = min(1.0, self.base_p_fail + (1 - self.base_p_fail) * dep_str)
                        if p_fail > 0.5:
                            new_failures.add(neighbor_id)
                            arrival_times[neighbor_id] = t_current + dt
                            
            if not new_failures:
                break
                
            failed_nodes.update(new_failures)
            
        intensities = {nid: 1.0 for nid in failed_nodes}
        peak = 1.0 if failed_nodes else 0.0
        
        return PropagationResult(
            affected_nodes=intensities,
            arrival_times_minutes=arrival_times,
            peak_intensity=peak,
            confidence=0.75,
            model_type=self.model_type(),
        )

    def model_type(self) -> str:
        return "GRAPH_DIFFUSION"

    def applicable_hazard_types(self) -> list[str]:
        return ["POWER_FAILURE", "ELECTRICAL_FAULT"]
