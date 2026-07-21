from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.graphrag import (
    Citation,
    FusedEvidence,
    FusionWeights,
    GroundedAnswer,
    GraphRAGService,
    ParsedQuery,
    QueryIntent,
    QueryParser,
)
from app.modules.graphrag.context.builder import ContextBuilder
from app.modules.graphrag.generation.citations import assemble_citations
from app.modules.graphrag.generation.grounded_generation import GroundedAnswerGenerator
from app.modules.graphrag.ranking.fusion import fuse_evidence


def test_query_parser():
    """Verify QueryParser intent classification and entity extraction."""
    parsed = QueryParser.parse("Which workers are at risk if Tank T-12 develops a gas leak in Zone B?")
    assert parsed.intent == QueryIntent.RISK_ANALYSIS
    assert "Tank T-12" in parsed.entity_ids or "T-12" in str(parsed.entity_ids)
    assert "Worker" in parsed.entity_types or "Zone" in parsed.entity_types


def test_evidence_fusion_and_ranking():
    """Verify evidence fusion combines graph facts and vector documents with weighted scores."""
    graph_facts = [
        {"id": "T-12", "name": "Tank T-12", "entity_type": "Equipment", "status": "OPERATIONAL"},
        {"id": "Z-B", "name": "Zone B", "entity_type": "Zone"},
    ]
    vector_docs = [
        {"id": "doc_1", "text_content": "Gas Leak SOP evacuation rules", "similarity_score": 0.88},
    ]

    weights = FusionWeights(graph_distance=0.30, semantic_similarity=0.30)
    fused = fuse_evidence(graph_facts, vector_docs, weights)

    assert len(fused) == 3
    assert fused[0].fusion_score > 0.0
    assert fused[0].source_type in ("GRAPH", "DOCUMENT")


def test_context_builder():
    """Verify ContextBuilder deduplicates and formats context block."""
    items = [
        FusedEvidence(content="Tank T-12 in Zone B", source_type="GRAPH", source_id="T-12", fusion_score=0.9),
        FusedEvidence(content="SOP-12 evacuation plan", source_type="DOCUMENT", source_id="doc_1", fusion_score=0.85),
    ]

    block = ContextBuilder.build_context(items)
    assert "INDUSTRIAL KNOWLEDGE GRAPH & SAFETY CONTEXT" in block
    assert "Tank T-12 in Zone B" in block
    assert "SOP-12 evacuation plan" in block


def test_citations_assembler():
    """Verify CitationAssembler creates structured citations."""
    items = [
        FusedEvidence(content="Hazard HAZ-1 active", source_type="GRAPH", source_id="HAZ-1", fusion_score=0.95),
    ]
    citations = assemble_citations(items)
    assert len(citations) == 1
    assert citations[0].citation_id == 1
    assert citations[0].source_id == "HAZ-1"


@pytest.mark.asyncio
async def test_grounded_answer_generator():
    """Verify GroundedAnswerGenerator prompts LLMGateway."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Based on safety context, 5 workers are at risk in Zone B."
    mock_response.provider = "GeminiProvider"
    mock_response.model = "gemini-2.5-flash"
    mock_response.latency_ms = 120
    mock_response.input_tokens = 100
    mock_response.output_tokens = 30
    mock_llm.generate = AsyncMock(return_value=mock_response)

    generator = GroundedAnswerGenerator(llm_gateway=mock_llm)
    items = [
        FusedEvidence(content="Methane sensor active in Zone B", source_type="GRAPH", source_id="S-1", fusion_score=0.9)
    ]

    answer = await generator.generate_grounded_answer(
        question="Who is at risk in Zone B?",
        context_block="Context...",
        evidence_items=items,
    )

    assert "5 workers are at risk" in answer.answer
    assert answer.provider_used == "GeminiProvider"
    assert len(answer.citations) == 1


@pytest.mark.asyncio
async def test_graphrag_service_master_facade():
    """Verify GraphRAGService master facade orchestrates end-to-end flow."""
    mock_coord = AsyncMock()
    mock_coord.coordinate_retrieval.return_value = (
        [{"id": "EQ-1", "name": "Pump 1", "entity_type": "Equipment"}],
        [{"id": "doc_1", "text_content": "Pump maintenance manual", "similarity_score": 0.9}],
    )

    mock_gen = AsyncMock()
    mock_gen.generate_grounded_answer.return_value = GroundedAnswer(
        question="Is Pump 1 safe?",
        answer="Pump 1 is operational according to maintenance logs.",
        citations=[],
        evidence=[],
    )

    mock_cache = AsyncMock()
    mock_cache.get_cached_response.return_value = None
    mock_cache.cache_response.return_value = True

    service = GraphRAGService(
        coordinator=mock_coord,
        generator=mock_gen,
        cache=mock_cache,
    )

    answer = await service.answer("Is Pump 1 safe?")
    assert "Pump 1 is operational" in answer.answer
    mock_coord.coordinate_retrieval.assert_called_once()
    mock_gen.generate_grounded_answer.assert_called_once()
