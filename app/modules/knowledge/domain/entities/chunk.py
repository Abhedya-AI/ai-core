from pydantic import Field

from app.modules.knowledge.domain.entities.base import GraphEntity


class DocumentChunk(GraphEntity):
    """Text chunk vectorised for GraphRAG semantic search."""

    document_id: str
    chunk_index: int
    text_content: str
    token_count: int = 0
    embedding_id: str | None = None
    entity_type: str = Field(default="DocumentChunk")
