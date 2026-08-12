from __future__ import annotations
import networkx as nx
import numpy as np
from app.core.logging import get_logger

log = get_logger(__name__)

class EquipmentDependencyAnalyzer:
    """Analyzes equipment dependencies."""

    def __init__(self, knowledge_service=None) -> None:
        self._knowledge_service = knowledge_service

    async def build_equipment_dependency_graph(self, equipment_ids: list[str]) -> nx.DiGraph:
        """Build dependency graph for equipment."""
        graph = nx.DiGraph()
        
        for eq in equipment_ids:
            graph.add_node(eq, criticality=0.5)
            
        for i in range(len(equipment_ids) - 1):
            graph.add_edge(equipment_ids[i], equipment_ids[i+1])
            
        return graph

    async def find_critical_equipment(self, equipment_ids: list[str]) -> list[dict]:
        """Find critical equipment based on centrality."""
        graph = await self.build_equipment_dependency_graph(equipment_ids)
        if not graph:
            return []
            
        centrality = nx.betweenness_centrality(graph)
        scores = list(centrality.values())
        if not scores:
            return []
            
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        threshold = mean_score + std_score
        
        critical = []
        for eq_id, score in centrality.items():
            if score >= threshold:
                out_degree = graph.out_degree(eq_id)
                critical.append({
                    "equipment_id": eq_id,
                    "criticality_score": score,
                    "dependency_count": out_degree,
                    "is_single_point_of_failure": out_degree > 1 and graph.in_degree(eq_id) == 0
                })
                
        return critical

    def compute_failure_impact(self, equipment_id: str, dep_graph: nx.DiGraph) -> dict:
        """Compute impact of equipment failure."""
        if equipment_id not in dep_graph:
            return {}
            
        direct_deps = list(dep_graph.successors(equipment_id))
        transitive_deps = list(nx.descendants(dep_graph, equipment_id))
        
        score = len(transitive_deps) / max(1, len(dep_graph.nodes))
        
        return {
            "equipment_id": equipment_id,
            "direct_deps": direct_deps,
            "transitive_deps": transitive_deps,
            "failure_impact_score": score
        }

    def find_dependency_bottlenecks(self, dep_graph: nx.DiGraph) -> list[str]:
        """Find bottlenecks based on centrality > 0.5."""
        centrality = nx.betweenness_centrality(dep_graph)
        return [node for node, score in centrality.items() if score > 0.5]

    def simulate_equipment_failure(self, failed_id: str, dep_graph: nx.DiGraph, failure_probability: float) -> dict[str, float]:
        """Simulate propagating failure."""
        probs = {failed_id: failure_probability}
        
        if failed_id not in dep_graph:
            return probs
            
        for node in nx.bfs_tree(dep_graph, failed_id):
            if node == failed_id:
                continue
            parents = list(dep_graph.predecessors(node))
            parent_prob = max((probs.get(p, 0.0) for p in parents), default=0.0)
            probs[node] = parent_prob * failure_probability
            
        return probs
