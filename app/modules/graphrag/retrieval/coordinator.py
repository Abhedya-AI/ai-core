"""coordinator.py — Retrieval Coordinator orchestrating cache and hybrid search."""

from typing import Any

from app.core.logging import get_logger
from app.modules.graphrag.query.parser import ParsedQuery
from app.modules.graphrag.retrieval.cache import GraphRAGCache
from app.modules.graphrag.retrieval.hybrid_retriever import HybridRetriever

log = get_logger("graphrag.retrieval.coordinator")


class RetrievalCoordinator:
    """Master retrieval coordinator orchestrating cache lookup, graph retrieval, and vector search."""

    def __init__(
        self,
        hybrid_retriever: HybridRetriever | None = None,
        cache: GraphRAGCache | None = None,
    ) -> None:
        self._retriever = hybrid_retriever or HybridRetriever()
        self._cache = cache or GraphRAGCache()

    async def coordinate_retrieval(
        self,
        parsed_query: ParsedQuery,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Coordinate hybrid graph and vector retrieval.

        Returns:
            tuple[graph_facts, vector_documents]
        """
        log.info(f"Coordinating retrieval for query intent '{parsed_query.intent.value}'")
        return await self._retriever.retrieve_hybrid(parsed_query)
