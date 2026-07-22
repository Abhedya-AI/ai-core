"""embeddings.py — Phase 8: Async FAISS Vector Store & Embedding Generator."""

from app.core.logging import get_logger
from app.infrastructure.vectorstore.embeddings import EmbeddingService
from app.modules.agents.document.models import DocumentChunk

log = get_logger("agents.document.embeddings")


class AsyncEmbeddingEngine:
    """Phase 8: Asynchronously generates vector embeddings for chunks and indexes them into FAISS."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService.get()

    def generate_embeddings(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """
        Generate vector embeddings for DocumentChunk items.

        Returns:
            list of DocumentChunk objects enriched with embedding vectors.
        """
        for chunk in chunks:
            if not chunk.embedding:
                vector = self.embedding_service.encode_single(chunk.content)
                chunk.embedding = vector
        log.info(f"Generated embeddings for {len(chunks)} document chunks.")
        return chunks
