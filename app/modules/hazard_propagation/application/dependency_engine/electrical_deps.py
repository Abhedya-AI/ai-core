from __future__ import annotations
import networkx as nx
from app.core.logging import get_logger

log = get_logger(__name__)

class ElectricalDependencyAnalyzer:
    """Analyzes electrical dependencies."""

    def __init__(self, knowledge_service=None) -> None:
        self._knowledge_service = knowledge_service

    async def build_electrical_network(self, panel_ids: list[str], circuit_ids: list[str]) -> nx.DiGraph:
        """Build electrical network graph."""
        graph = nx.DiGraph()
        
        if not panel_ids:
            panel_ids = ["MAIN_PANEL"]
            
        for panel in panel_ids:
            graph.add_node(panel, type="panel", criticality=0.8)
            for circ in circuit_ids:
                graph.add_node(circ, type="circuit", criticality=0.5)
                graph.add_edge(panel, circ)
                
        return graph

    async def find_critical_panels(self, panel_ids: list[str]) -> list[dict]:
        """Find panels with most downstream circuits."""
        graph = await self.build_electrical_network(panel_ids, [f"C{i}" for i in range(5)])
        
        critical = []
        for panel in panel_ids:
            if panel in graph:
                circuits = len(list(nx.descendants(graph, panel)))
                critical.append({
                    "panel_id": panel,
                    "circuit_count": circuits,
                    "criticality_score": circuits * 0.1
                })
                
        return sorted(critical, key=lambda x: x["circuit_count"], reverse=True)

    def simulate_power_failure(self, failed_panel_id: str, network: nx.DiGraph) -> list[str]:
        """Get all affected nodes from power failure."""
        if failed_panel_id not in network:
            return []
        return list(nx.descendants(network, failed_panel_id))

    def compute_power_restoration_priority(self, network: nx.DiGraph, affected_equipment: list[str]) -> list[dict]:
        """Compute restoration priority order."""
        to_restore = []
        for eq in affected_equipment:
            if eq in network:
                crit = network.nodes[eq].get("criticality", 0.5)
                to_restore.append({
                    "equipment_id": eq,
                    "criticality": crit
                })
                
        to_restore.sort(key=lambda x: x["criticality"], reverse=True)
        
        for i, item in enumerate(to_restore):
            item["restoration_order"] = i + 1
            
        return to_restore

    def estimate_outage_impact(self, failed_panels: list[str], network: nx.DiGraph) -> dict:
        """Estimate impact of outages."""
        affected = set()
        for p in failed_panels:
            if p in network:
                affected.update(nx.descendants(network, p))
                
        safety_critical = 0
        for node in affected:
            if network.nodes[node].get("criticality", 0.0) > 0.7:
                safety_critical += 1
                
        total_nodes = len(network.nodes)
        pct = (len(affected) / max(1, total_nodes)) * 100.0
        
        return {
            "affected_equipment_count": len(affected),
            "safety_critical_systems_affected": safety_critical,
            "production_impact_pct": pct
        }
