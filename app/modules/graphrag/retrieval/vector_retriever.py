"""vector_retriever.py — FAISS Vector Store Retriever."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.vectorstore.embeddings import EmbeddingService
from app.infrastructure.vectorstore.faiss import FAISSVectorStore
from app.modules.graphrag.query.parser import ParsedQuery

log = get_logger("graphrag.retrieval.vector")


class VectorRetriever:
    """Retrieves semantically related document chunks and SOPs from FAISS vector store."""

    def __init__(self, vector_store: FAISSVectorStore | None = None) -> None:
        self._store = vector_store or FAISSVectorStore()
        self._embeddings = EmbeddingService.get()

    async def retrieve_documents(self, parsed_query: ParsedQuery, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Embed query text and search top_k semantically similar document chunks.

        Returns:
            list of document chunk metadata dicts with similarity scores.
        """
        try:
            query_vec = self._embeddings.encode_single(parsed_query.raw_query)
            results = self._store.search(query_vec, top_k=top_k)
            docs = []
            for r in results:
                meta = dict(r.get("metadata", {}))
                meta["similarity_score"] = r.get("score", 0.0)
                meta["_retrieved_via"] = "vector_search"
                docs.append(meta)
            return docs
        except Exception as exc:
            log.warning(f"Vector retrieval failed: {exc}")
            return []
