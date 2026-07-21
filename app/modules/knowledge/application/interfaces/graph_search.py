"""
graph_search.py — Abstract Interface for Graph Search Engine (IGraphSearchEngine).
"""

from abc import ABC, abstractmethod
from typing import Any

from app.modules.knowledge.application.dto import GraphSearchRequest, TraversalRequest, TraversalResult


class IGraphSearchEngine(ABC):
    """Abstract interface for advanced graph search and pathfinding queries."""

    @abstractmethod
    async def search(self, request: GraphSearchRequest) -> list[dict[str, Any]]:
        """Structured pattern search across graph nodes and relationships."""

    @abstractmethod
    async def find_shortest_path(self, start_id: str, target_id: str, max_depth: int = 5) -> list[dict[str, Any]]:
        """Find the shortest path between two nodes."""

    @abstractmethod
    async def get_subgraph(self, center_node_id: str, depth: int = 2) -> TraversalResult:
        """Extract a sub-graph centered around a target node."""
