from __future__ import annotations
import networkx as nx
from app.core.logging import get_logger

log = get_logger(__name__)

class ZoneDependencyAnalyzer:
    """Analyzes zone dependencies."""

    def __init__(self, knowledge_service=None) -> None:
        self._knowledge_service = knowledge_service

    async def build_zone_dependency_graph(self, zone_ids: list[str]) -> nx.DiGraph:
        """Build zone dependency graph."""
        graph = nx.DiGraph()
        
        for zone in zone_ids:
            graph.add_node(zone)
            
        n = len(zone_ids)
        for i, zone in enumerate(zone_ids):
            if n > 1:
                graph.add_edge(zone, zone_ids[(i+1)%n], resource_shared=True, pipe_connected=False, ventilation_linked=True)
            if n > 2:
                graph.add_edge(zone, zone_ids[(i+2)%n], resource_shared=False, pipe_connected=True, ventilation_linked=False)
                
        return graph

    async def find_critical_zones(self, zone_ids: list[str]) -> list[dict]:
        """Find critical zones based on degree centrality."""
        graph = await self.build_zone_dependency_graph(zone_ids)
        
        if not graph:
            return []
            
        centrality = nx.degree_centrality(graph)
        
        critical = []
        for zone, score in centrality.items():
            degree = graph.degree(zone)
            critical.append({
                "zone_id": zone,
                "criticality_score": score,
                "connection_count": degree,
                "is_evacuation_chokepoint": degree > 3
            })
            
        return sorted(critical, key=lambda x: x["criticality_score"], reverse=True)

    def compute_zone_isolation_impact(self, zone_id: str, dep_graph: nx.DiGraph) -> dict:
        """Compute impact of isolating a zone."""
        if zone_id not in dep_graph:
            return {}
            
        neighbors = list(dep_graph.neighbors(zone_id))
        degree = len(neighbors)
        total = len(dep_graph.nodes)
        
        return {
            "zone_id": zone_id,
            "affected_zones": neighbors,
            "isolation_impact_score": degree / max(1, total)
        }

    def find_shared_resources(self, zone_id: str, dep_graph: nx.DiGraph) -> list[str]:
        """Find neighbors sharing resources."""
        shared = []
        if zone_id in dep_graph:
            for neighbor in dep_graph.neighbors(zone_id):
                if dep_graph.edges[zone_id, neighbor].get("resource_shared", False):
                    shared.append(neighbor)
        return shared

    def rank_zones_by_hazard_vulnerability(self, zones: list[dict]) -> list[dict]:
        """Rank zones by vulnerability."""
        return sorted(zones, key=lambda x: x.get("exposure_score", 0.0), reverse=True)
