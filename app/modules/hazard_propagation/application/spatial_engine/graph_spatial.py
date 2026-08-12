from __future__ import annotations
import networkx as nx
from app.core.logging import get_logger

log = get_logger(__name__)

class GraphSpatialEngine:
    """Graph-based spatial engine for hazard propagation."""
    
    def __init__(self) -> None:
        pass
    
    def build_graph(self, nodes: list[dict], edges: list[dict]) -> nx.DiGraph:
        """Build directed graph. Node attrs: intensity=0.0. Edge attrs: resistance, distance."""
        graph = nx.DiGraph()
        for node in nodes:
            node_id = node.get("node_id")
            if node_id:
                graph.add_node(node_id, intensity=0.0, **node)
        
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src and tgt:
                res = edge.get("resistance", 0.0)
                dist = edge.get("distance", 1.0)
                graph.add_edge(src, tgt, resistance=res, distance=dist)
                
        return graph
    
    def diffuse_hazard(
        self, graph: nx.DiGraph, source_id: str, initial_intensity: float,
        steps: int, decay: float = 0.9
    ) -> dict[str, float]:
        """Iterative graph diffusion. Returns {node_id: final_intensity}."""
        if source_id not in graph:
            return {}
            
        intensities = {n: 0.0 for n in graph.nodes}
        intensities[source_id] = initial_intensity
        
        for _ in range(steps):
            new_intensities = intensities.copy()
            for u in graph.nodes:
                curr_i = intensities[u]
                if curr_i > 0.01:
                    for v in graph.successors(u):
                        res = graph.edges[u, v].get("resistance", 0.0)
                        diff = curr_i * (1 - res) * decay * 0.1
                        new_intensities[v] = min(1.0, new_intensities[v] + diff)
            intensities = new_intensities
            
        return intensities
    
    def compute_shortest_safe_path(
        self, graph: nx.DiGraph, source: str, target: str
    ) -> list[str]:
        """Dijkstra with edges weighted by resistance. Falls back to [] if no path."""
        try:
            return nx.shortest_path(graph, source, target, weight="resistance")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def find_reachable_nodes(
        self, graph: nx.DiGraph, source: str, intensity_threshold: float = 0.05
    ) -> list[str]:
        """BFS to find nodes that receive threshold+ intensity."""
        reachable = []
        if source not in graph:
            return reachable
            
        intensities = self.diffuse_hazard(graph, source, 1.0, steps=10, decay=0.9)
        for node_id, intensity in intensities.items():
            if intensity >= intensity_threshold:
                reachable.append(node_id)
        return reachable
    
    def compute_centrality(self, graph: nx.DiGraph) -> dict[str, float]:
        """Betweenness centrality for all nodes."""
        if not graph:
            return {}
        try:
            return nx.betweenness_centrality(graph, weight="distance")
        except Exception:
            return {n: 0.0 for n in graph.nodes}
    
    def get_high_centrality_nodes(self, graph: nx.DiGraph, top_n: int = 5) -> list[str]:
        """Return top N nodes by centrality score."""
        centrality = self.compute_centrality(graph)
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return [node_id for node_id, _ in sorted_nodes[:top_n]]
