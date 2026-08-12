from __future__ import annotations
import time
import uuid
import networkx as nx
from typing import Any
from app.core.logging import get_logger
from app.modules.digital_twin.application.optimization.base import AbstractOptimizer, OptimizationResult

log = get_logger(__name__)

class ResourceDeploymentOptimizer(AbstractOptimizer):
    def get_target(self) -> str:
        return "RESOURCE_DEPLOYMENT"

    def get_objective(self) -> str:
        return "Optimize resource placement to maximize emergency response readiness"

    async def optimize(self, twin_state: dict[str, Any], constraints: dict[str, Any], graphrag_service: Any) -> OptimizationResult:
        t0 = time.perf_counter()
        optimization_id = str(uuid.uuid4())
        
        try:
            resource_states = twin_state.get("resource_states", {})
            zone_states = twin_state.get("zone_states", {})
            
            G = nx.Graph()
            for z_id, z_data in zone_states.items():
                G.add_node(z_id, risk=z_data.get("risk_score", 0.0))
                for neighbor in z_data.get("neighbors", []):
                    G.add_edge(z_id, neighbor)
                    
            high_risk_zones = [n for n, d in G.nodes(data=True) if d.get('risk', 0.0) > 0.6]
            
            placements = {}
            uncovered_high_risk = set(high_risk_zones)
            
            for res_id, res_data in resource_states.items():
                if not uncovered_high_risk:
                    break
                    
                best_zone = None
                best_coverage = 0
                
                for zone in G.nodes():
                    # Coverage: within 2 hops
                    covered = set(nx.single_source_shortest_path_length(G, zone, cutoff=2).keys())
                    overlap = covered.intersection(uncovered_high_risk)
                    if len(overlap) > best_coverage:
                        best_coverage = len(overlap)
                        best_zone = zone
                        
                if best_zone:
                    placements[res_id] = best_zone
                    covered_nodes = set(nx.single_source_shortest_path_length(G, best_zone, cutoff=2).keys())
                    uncovered_high_risk -= covered_nodes
                    
            coverage_pct = 100.0
            if high_risk_zones:
                coverage_pct = ((len(high_risk_zones) - len(uncovered_high_risk)) / len(high_risk_zones)) * 100
                
            solution = {
                "placements": placements,
                "coverage_pct": coverage_pct,
                "uncovered_high_risk_zones": list(uncovered_high_risk),
                "deployment_priority": "HIGH"
            }
            
            latency_ms = (time.perf_counter() - t0) * 1000
            
            return OptimizationResult(
                optimization_id=optimization_id,
                target=self.get_target(),
                status="SUCCESS",
                objective=self.get_objective(),
                solution=solution,
                improvement_score=coverage_pct / 100.0,
                baseline_score=0.0,
                optimized_score=coverage_pct,
                optimization_steps=[],
                graphrag_citations=[],
                risk_references=[],
                reasoning="Deployed resources to cover maximum number of high-risk zones within 2 hops.",
                recommended_actions=["Move resources to designated zones"],
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
