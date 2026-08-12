"""
use_cases/search_use_cases.py — Search Use Cases.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.modules.knowledge.application.dto.search_dto import (
    SearchRequest,
    SearchResult,
)
from app.modules.knowledge.services.graph_search_service import GraphSearchService

log = get_logger("knowledge.use_case.search")


class SearchKnowledgeGraphUseCase:
    """Use case: Execute full-text, property, structural, or proximity search on the Knowledge Graph."""

    def __init__(self, service: GraphSearchService | None = None) -> None:
        self._service = service or GraphSearchService()

    async def execute(self, request: SearchRequest) -> SearchResult:
        """Execute graph search."""
        return await self._service.search(request)
