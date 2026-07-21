"""
graphrag_service.py — Master GraphRAG Service Facade.

Single entry point for Knowledge Graph + Vector retrieval, evidence fusion,
and grounded LLM generation.
"""

import time
from typing import Any

from app.core.logging import get_logger
from app.modules.graphrag.context.builder import ContextBuilder
from app.modules.graphrag.generation.grounded_generation import GroundedAnswer, GroundedAnswerGenerator
from app.modules.graphrag.query.parser import QueryParser
from app.modules.graphrag.ranking.evidence_ranker import EvidenceRanker
from app.modules.graphrag.retrieval.cache import GraphRAGCache
from app.modules.graphrag.retrieval.coordinator import RetrievalCoordinator

log = get_logger("graphrag.service.facade")


class GraphRAGService:
    """
    Master facade for GraphRAG operations.

    Orchestrates Query Parsing -> Hybrid Retrieval -> Evidence Fusion ->
    Context Compression -> Grounded Generation.
    """

    def __init__(
        self,
        coordinator: RetrievalCoordinator | None = None,
        ranker: EvidenceRanker | None = None,
        generator: GroundedAnswerGenerator | None = None,
        cache: GraphRAGCache | None = None,
    ) -> None:
        self.coordinator = coordinator or RetrievalCoordinator()
        self.ranker = ranker or EvidenceRanker()
        self.generator = generator or GroundedAnswerGenerator()
        self.cache = cache or GraphRAGCache()

    async def answer(
        self,
        question: str,
        user_context: dict[str, Any] | None = None,
    ) -> GroundedAnswer:
        """
        Execute the complete GraphRAG pipeline for a user question.

        Args:
            question: Natural language query string.
            user_context: Optional context dictionary.

        Returns:
            GroundedAnswer DTO containing grounded text, citations, and evidence metrics.
        """
        start_time = time.perf_counter()
        log.info(f"GraphRAG answering: '{question}'")

        # 1. Cache Check
        cache_key = f"q:{hash(question)}"
        cached = await self.cache.get_cached_response(cache_key)
        if cached:
            log.info("GraphRAG cache hit!")
            return GroundedAnswer.model_validate(cached)

        # 2. Query Parsing & Intent Extraction
        parsed_query = QueryParser.parse(question)
        log.info(f"Parsed intent: {parsed_query.intent.value}, extracted entities: {parsed_query.entity_ids}")

        # 3. Hybrid Retrieval (Graph Facts + Vector Documents)
        graph_facts, vector_docs = await self.coordinator.coordinate_retrieval(parsed_query)

        # 4. Multi-Factor Evidence Fusion & Ranking
        fused_evidence = self.ranker.rank_evidence(graph_facts, vector_docs, top_n=8)

        # 5. Context Construction & Compression
        context_block = ContextBuilder.build_context(fused_evidence, max_items=8)

        # 6. Grounded Answer Generation via LLMGateway
        answer = await self.generator.generate_grounded_answer(
            question=question,
            context_block=context_block,
            evidence_items=fused_evidence,
        )

        total_latency = int((time.perf_counter() - start_time) * 1000)
        answer.latency_ms = total_latency
        answer.metadata["graph_facts_retrieved"] = len(graph_facts)
        answer.metadata["vector_docs_retrieved"] = len(vector_docs)

        # 7. Cache Response
        await self.cache.cache_response(cache_key, answer.model_dump(), ttl=300)

        return answer
