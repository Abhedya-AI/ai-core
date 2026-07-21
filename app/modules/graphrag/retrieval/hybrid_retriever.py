"""hybrid_retriever.py — Hybrid Retriever combining Graph and Vector search."""

from typing import Any

from app.modules.graphrag.query.parser import ParsedQuery
from app.modules.graphrag.retrieval.graph_retriever import GraphRetriever
from app.modules.graphrag.retrieval.vector_retriever import VectorRetriever


class HybridRetriever:
    """Executes parallel hybrid retrieval combining Knowledge Graph facts and Vector document chunks."""

    def __init__(
        self,
        graph_retriever: GraphRetriever | None = None,
        vector_retriever: VectorRetriever | None = None,
    ) -> None:
        self.graph_retriever = graph_retriever or GraphRetriever()
        self.vector_retriever = vector_retriever or VectorRetriever()

    async def retrieve_hybrid(
        self,
        parsed_query: ParsedQuery,
        graph_depth: int = 2,
        vector_top_k: int = 5,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Execute parallel hybrid retrieval.

        Returns:
            tuple[graph_facts, vector_documents]
        """
        graph_facts = await self.graph_retriever.retrieve_graph_facts(parsed_query, max_depth=graph_depth)
        vector_docs = await self.vector_retriever.retrieve_documents(parsed_query, top_k=vector_top_k)
        return graph_facts, vector_docs
