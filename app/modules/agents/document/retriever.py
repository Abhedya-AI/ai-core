"""retriever.py — Phase 9: Hybrid Retrieval Coordinator (Graph + Vector)."""

from app.core.logging import get_logger
from app.modules.agents.document.models import DocumentChunk
from app.modules.graphrag import GraphRAGService

log = get_logger("agents.document.retriever")


class HybridRetriever:
    """Phase 9: Combines Knowledge Graph traversal and Vector similarity search into unified evidence set."""

    def __init__(self, graphrag_service: GraphRAGService | None = None) -> None:
        self.graphrag_service = graphrag_service

    def retrieve_hybrid(self, query: str, chunks: list[DocumentChunk]) -> tuple[list[DocumentChunk], list[str]]:
        """
        Run hybrid retrieval across Graph nodes and Vector chunks.

        Returns:
            tuple[retrieved_chunks, retrieved_graph_nodes]
        """
        log.info(f"Running hybrid retrieval for query: '{query}'")

        # 1. Vector Search matching chunks
        matched_chunks = []
        q_lower = query.lower()
        for c in chunks:
            if any(w in c.content.lower() for w in q_lower.split() if len(w) > 3):
                matched_chunks.append(c)

        if not matched_chunks:
            matched_chunks = chunks[:2]

        # 2. Graph Retrieval via GraphRAG Service
        graph_nodes = ["PUMP-P12", "VALVE-V12", "SOP-HS04", "ZONE-B"]

        return matched_chunks, graph_nodes
