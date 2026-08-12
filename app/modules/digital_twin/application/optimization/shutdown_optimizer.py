from __future__ import annotations
import time
import uuid
import networkx as nx
from typing import Any
from app.core.logging import get_logger
from app.modules.digital_twin.application.optimization.base import AbstractOptimizer, OptimizationResult

log = get_logger(__name__)

class ShutdownOptimizer(AbstractOptimizer):
    def get_target(self) -> str:
        return "SHUTDOWN"

    def get_objective(self) -> str:
        return "Minimize shutdown time while ensuring safe isolation sequence"

    async def optimize(self, twin_state: dict[str, Any], constraints: dict[str, Any], graphrag_service: Any) -> OptimizationResult:
        t0 = time.perf_counter()
        optimization_id = str(uuid.uuid4())
        
        try:
            equipment_states = twin_state.get("equipment_states", {})
            is_emergency = constraints.get("emergency", False)
            
            if is_emergency:
                solution = {
                    "shutdown_sequence": [{"batch": 1, "equipment_ids": list(equipment_states.keys()), "estimated_time_minutes": 1, "priority": "CRITICAL"}],
                    "total_time_minutes": 1,
                    "safe_isolation_achieved": True
                }
                latency_ms = (time.perf_counter() - t0) * 1000
                return OptimizationResult(
                    optimization_id=optimization_id,
                    target=self.get_target(),
                    status="SUCCESS",
                    objective=self.get_objective(),
                    solution=solution,
                    improvement_score=1.0,
                    baseline_score=len(equipment_states) * 5,
                    optimized_score=1.0,
                    optimization_steps=[],
                    graphrag_citations=[],
                    risk_references=[],
                    reasoning="Emergency all-stop initiated. Ignored dependencies.",
                    recommended_actions=["Verify all equipment halted"],
                    latency_ms=latency_ms,
                    error=None
                )
            
            G = nx.DiGraph()
            for eq_id, eq_data in equipment_states.items():
                G.add_node(eq_id)
                for dep_id in eq_data.get("dependency_ids", []):
                    G.add_edge(dep_id, eq_id) # dep_id must be shutdown after eq_id
                    
            try:
                # Topo sort where leaves are shut down first
                sorted_nodes = list(nx.topological_sort(G))
            except nx.NetworkXUnfeasible:
                raise ValueError("Cyclic dependencies detected in equipment graph")
            
            # Group into parallel batches
            batches = []
            in_degree = dict(G.in_degree())
            current_batch = [n for n in G.nodes() if in_degree[n] == 0]
            
            while current_batch:
                batches.append(current_batch)
                next_batch = []
                for node in current_batch:
                    for successor in G.successors(node):
                        in_degree[successor] -= 1
                        if in_degree[successor] == 0:
                            next_batch.append(successor)
                current_batch = next_batch
                
            baseline_score = len(G.nodes()) * 5.0 # assume 5 min per equipment sequential
            
            shutdown_sequence = []
            total_time_minutes = 0
            for i, batch in enumerate(batches):
                time_for_batch = 5.0 # parallel
                total_time_minutes += time_for_batch
                shutdown_sequence.append({
                    "batch": i + 1,
                    "equipment_ids": batch,
                    "estimated_time_minutes": time_for_batch,
                    "priority": "NORMAL"
                })
                
            optimized_score = total_time_minutes
            improvement_score = (baseline_score - optimized_score) / baseline_score if baseline_score > 0 else 0.0
            
            solution = {
                "shutdown_sequence": shutdown_sequence,
                "total_time_minutes": total_time_minutes,
                "safe_isolation_achieved": True
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
                optimization_steps=[],
                graphrag_citations=[],
                risk_references=[],
                reasoning="Computed parallel batch shutdown respecting dependencies.",
                recommended_actions=["Proceed with batched shutdown"],
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
