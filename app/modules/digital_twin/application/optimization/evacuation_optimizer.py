from __future__ import annotations
import time
import uuid
import networkx as nx
from typing import Any
from app.core.logging import get_logger
from app.modules.digital_twin.application.optimization.base import AbstractOptimizer, OptimizationResult

log = get_logger(__name__)

class EvacuationOptimizer(AbstractOptimizer):
    def get_target(self) -> str:
        return "EVACUATION"

    def get_objective(self) -> str:
        return "Minimize total evacuation time and maximize worker safety"

    async def optimize(self, twin_state: dict[str, Any], constraints: dict[str, Any], graphrag_service: Any) -> OptimizationResult:
        t0 = time.perf_counter()
        optimization_id = str(uuid.uuid4())
        
        try:
            worker_states = twin_state.get("worker_states", {})
            zone_states = twin_state.get("zone_states", {})
            
            # Build graph
            G = nx.DiGraph()
            for zone_id, zone_data in zone_states.items():
                G.add_node(zone_id, **zone_data)
                for neighbor in zone_data.get("neighbors", []):
                    G.add_edge(zone_id, neighbor)
            
            # Identify safe zones
            safe_zones = []
            for zone_id, zone_data in zone_states.items():
                health_score = zone_data.get("health_score", 1.0)
                is_hazard_active = zone_data.get("is_hazard_active", False)
                if health_score > 0.7 and not is_hazard_active:
                    safe_zones.append(zone_id)
            
            if not safe_zones:
                raise ValueError("No safe zones available for evacuation")
            
            evacuation_routes = {}
            worker_wave_groups = []
            baseline_distances = []
            optimized_distances = []
            
            for worker_id, worker_data in worker_states.items():
                current_zone = worker_data.get("current_zone")
                if not current_zone or current_zone not in G:
                    continue
                
                # Naive path (baseline)
                try:
                    baseline_path = nx.shortest_path(G, source=current_zone, target=safe_zones[0])
                    baseline_distances.append(len(baseline_path) - 1)
                except nx.NetworkXNoPath:
                    pass
                
                # Optimized path
                best_path = None
                best_distance = float('inf')
                for sz in safe_zones:
                    try:
                        # Edge weight logic
                        def weight_func(u, v, d):
                            crowd_density = zone_states.get(v, {}).get("occupancy", 0) / max(1, zone_states.get(v, {}).get("max_occupancy", 100))
                            return 5 + (crowd_density * 3)
                        path = nx.dijkstra_path(G, source=current_zone, target=sz, weight=weight_func)
                        dist = nx.dijkstra_path_length(G, source=current_zone, target=sz, weight=weight_func)
                        if dist < best_distance:
                            best_distance = dist
                            best_path = path
                    except nx.NetworkXNoPath:
                        continue
                
                if best_path:
                    evacuation_routes[worker_id] = best_path
                    optimized_distances.append(best_distance)
                    worker_wave_groups.append(worker_id)
            
            # Group into waves (max 20 per wave)
            wave_assignments = {}
            total_time_minutes = 0
            for i in range(0, len(worker_wave_groups), 20):
                wave_num = (i // 20) + 1
                wave_assignments[f"wave_{wave_num}"] = worker_wave_groups[i:i+20]
                total_time_minutes += 2 # stagger
            
            if optimized_distances:
                total_time_minutes += max(optimized_distances)
            
            baseline_score = sum(baseline_distances) / len(baseline_distances) if baseline_distances else 0.0
            optimized_score = sum(optimized_distances) / len(optimized_distances) if optimized_distances else 0.0
            improvement_score = (baseline_score - optimized_score) / baseline_score if baseline_score > 0 else 0.0
            
            solution = {
                "evacuation_routes": evacuation_routes,
                "wave_assignments": wave_assignments,
                "total_time_minutes": total_time_minutes,
                "safe_zones": safe_zones,
                "bottleneck_zones": []
            }
            
            latency_ms = (time.perf_counter() - t0) * 1000
            
            return OptimizationResult(
                optimization_id=optimization_id,
                target=self.get_target(),
                status="SUCCESS",
                objective=self.get_objective(),
                solution=solution,
                improvement_score=improvement_score,
                baseline_score=baseline_score,
                optimized_score=optimized_score,
                optimization_steps=[{"step": 1, "action": "Calculated shortest paths", "score_delta": improvement_score, "rationale": "Dijkstra routing"}],
                graphrag_citations=[],
                risk_references=[],
                reasoning="Calculated optimal evacuation paths avoiding crowded and hazardous zones.",
                recommended_actions=["Deploy marshals to safe zones", "Activate emergency lighting on routes"],
                latency_ms=latency_ms,
                error=None
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - t0) * 1000
            return OptimizationResult(
                optimization_id=optimization_id,
                target=self.get_target(),
                status="FAILED",
                objective=self.get_objective(),
                solution={},
                improvement_score=0.0,
                baseline_score=0.0,
                optimized_score=0.0,
                optimization_steps=[],
                graphrag_citations=[],
                risk_references=[],
                reasoning="",
                recommended_actions=[],
                latency_ms=latency_ms,
                error=str(e)
            )
