import pytest

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.document import (
    CitationEngine,
    DocumentAgent,
    DocumentAgentResult,
    DocumentIngestionEngine,
    DocumentParser,
    EntityExtractor,
    SemanticChunker,
)


def test_ingestion_parsing_chunking_and_entities():
    """Verify DocumentIngestion, DocumentParser, SemanticChunker, and EntityExtractor."""
    doc = DocumentIngestionEngine.ingest_document("SOP-HS-04.pdf", "PDF")
    assert doc.doc_id.startswith("DOC-")

    parsed = DocumentParser.parse(doc)
    assert "pages" in parsed

    chunks = SemanticChunker.chunk_document(doc, parsed)
    assert len(chunks) >= 2
    assert chunks[1].parent_chunk_id == chunks[0].chunk_id

    entities = EntityExtractor.extract_entities(chunks[1].content)
    assert len(entities) >= 4
    entity_names = [e.entity_name for e in entities]
    assert "Pump P-12" in entity_names
    assert "Valve V-12" in entity_names

    citations = CitationEngine.build_citations(chunks)
    assert len(citations) >= 1
    assert "SOP" in citations[0].doc_title


@pytest.mark.asyncio
async def test_document_agent_end_to_end_execution():
    """Verify DocumentAgent 12-phase GraphRAG end-to-end execution returning DocumentAgentResult."""
    agent = DocumentAgent()
    ctx = AgentContext(
        query="What is the maintenance procedure for Pump P-12?",
        target_entity_id="SOP-HS-04.pdf",
    )

    result = await agent.execute(ctx)
    assert isinstance(result, DocumentAgentResult)
    assert result.success is True
    assert len(result.ingested_documents) == 1
    assert len(result.retrieved_chunks) >= 1
    assert len(result.citations) >= 1
    assert "Pump P-12" in result.grounded_answer.answer_text
    assert "Valve V-12" in result.grounded_answer.answer_text

    event_types = [e.event_type for e in result.events]
    assert "DocumentIndexed" in event_types
    assert "KnowledgeExtracted" in event_types
    assert "EmbeddingCreated" in event_types
    assert "GraphUpdated" in event_types
