"""traversal_service.py — Multi-hop graph traversal and pathfinding service."""

from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.application.dto import TraversalRequest, TraversalResult
from app.modules.knowledge.infrastructure.repositories.graph_repository import Neo4jGraphRepository

log = get_logger("knowledge.services.traversal")


class TraversalService:
    """Service providing K-hop expansion, shortest paths, and subgraph extractions."""

    def __init__(self, repository: Neo4jGraphRepository | None = None) -> None:
        self._repo = repository or Neo4jGraphRepository()

    async def traverse_khop(self, start_node_id: str, max_depth: int = 3) -> TraversalResult:
        """Perform K-hop expansion starting from start_node_id."""
        req = TraversalRequest(start_node_id=start_node_id, max_depth=max_depth)
        return await self._repo.traverse(req)

    async def find_shortest_path(self, start_id: str, target_id: str, max_depth: int = 5) -> list[dict[str, Any]]:
        """Find the shortest path between start_id and target_id."""
        return await self._repo.find_shortest_path(start_id, target_id, max_depth)

    async def get_subgraph(self, center_node_id: str, depth: int = 2) -> TraversalResult:
        """Extract a sub-graph snapshot centered around center_node_id."""
        return await self._repo.get_subgraph(center_node_id, depth)
