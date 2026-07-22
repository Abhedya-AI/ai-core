"""models.py — Document Intelligence & GraphRAG Agent Domain Models & DTOs."""

from typing import Any

from pydantic import BaseModel, Field

from app.modules.agents.core.agent_result import AgentResult


class DocumentChunk(BaseModel):
    """Semantic document chunk item."""

    chunk_id: str
    doc_id: str
    section_title: str = ""
    content: str
    page_number: int | None = 1
    parent_chunk_id: str | None = None
    embedding: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedEntity(BaseModel):
    """Domain entity extracted from document text."""

    entity_name: str
    entity_type: str = Field(..., description="EQUIPMENT, REGULATION, HAZARD, ZONE, WORKER_ROLE, CHEMICAL")
    canonical_id: str
    confidence: float = 0.92


class CitationSource(BaseModel):
    """Auditable document citation reference."""

    doc_title: str
    section: str
    source_type: str = "SOP"
    doc_id: str


class GroundedAnswer(BaseModel):
    """LLM answer grounded with citations and graph evidence."""

    answer_text: str
    citations: list[CitationSource] = Field(default_factory=list)
    graph_evidence_nodes: list[str] = Field(default_factory=list)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.95


class IngestedDocument(BaseModel):
    """Document metadata and parsed representation."""

    doc_id: str
    title: str
    file_type: str = "PDF"
    source_uri: str = "local"
    version: str = "1.0.0"
    author: str = "Safety Ops"
    chunks: list[DocumentChunk] = Field(default_factory=list)
    extracted_entities: list[ExtractedEntity] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentAgentResult(AgentResult):
    """Domain-extended result returned by Document Intelligence Agent."""

    grounded_answer: GroundedAnswer = Field(default_factory=GroundedAnswer)
    ingested_documents: list[IngestedDocument] = Field(default_factory=list)
    retrieved_chunks: list[DocumentChunk] = Field(default_factory=list)
    citations: list[CitationSource] = Field(default_factory=list)
