"""search_service.py — Structured pattern search service."""

from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.application.dto import GraphSearchRequest, NodeMatchCriteria
from app.modules.knowledge.infrastructure.repositories.graph_repository import Neo4jGraphRepository

log = get_logger("knowledge.services.search")


class SearchService:
    """Service executing structured pattern searches and filtering across knowledge graph nodes."""

    def __init__(self, repository: Neo4jGraphRepository | None = None) -> None:
        self._repo = repository or Neo4jGraphRepository()

    async def search_by_label(self, label: str, properties: dict[str, Any] | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Search nodes matching a specific entity label and property filters."""
        req = GraphSearchRequest(
            start_criteria=NodeMatchCriteria(label=label, properties=properties or {}),
            limit=limit,
        )
        return await self._repo.search(req)

    async def find_node_by_id(self, node_id: str) -> dict[str, Any] | None:
        """Fetch node by unique ID."""
        return await self._repo.find_by_id(node_id)
