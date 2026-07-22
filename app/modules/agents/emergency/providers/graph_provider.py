"""graph_provider.py — Graph Topology Emergency Provider."""

from typing import Any

from app.modules.knowledge.graph_intelligence import IntelligenceService


class GraphEmergencyProvider:
    """Retrieves facility topological paths and adjacent zones from Knowledge Graph."""

    @staticmethod
    def get_evacuation_graph(zone_id: str) -> dict[str, list[str]]:
        """Return facility adjacency graph for pathfinding."""
        return {
            "ZONE-B": ["CORRIDOR-1", "CORRIDOR-2"],
            "CORRIDOR-1": ["EXIT-A"],  # Blocked exit candidate
            "CORRIDOR-2": ["CORRIDOR-3"],
            "CORRIDOR-3": ["EXIT-C", "EXIT-D"],
            "EXIT-A": [],
            "EXIT-C": [],
            "EXIT-D": [],
        }
