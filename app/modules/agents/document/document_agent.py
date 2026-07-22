"""
document_agent.py — Master Document Intelligence & GraphRAG Agent.

Converts unstructured industrial documents into queryable Knowledge Graph nodes and FAISS vectors.
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.types import Capability
from app.modules.agents.document.answer_generator import GroundedAnswerGenerator
from app.modules.agents.document.chunker import SemanticChunker
from app.modules.agents.document.citation import CitationEngine
from app.modules.agents.document.confidence import DocumentConfidenceEngine
from app.modules.agents.document.context_builder import ContextBuilder
from app.modules.agents.document.embeddings import AsyncEmbeddingEngine
from app.modules.agents.document.entity_extractor import EntityExtractor
from app.modules.agents.document.events import DocumentEventGenerator
from app.modules.agents.document.explanation import DocumentExplanationGenerator
from app.modules.agents.document.graph_linker import KnowledgeGraphLinker
from app.modules.agents.document.ingestion import DocumentIngestionEngine
from app.modules.agents.document.metadata import MetadataExtractor
from app.modules.agents.document.models import DocumentAgentResult
from app.modules.agents.document.parser import DocumentParser
from app.modules.agents.document.reranker import EvidenceReranker
from app.modules.agents.document.retriever import HybridRetriever

log = get_logger("agents.document.orchestrator")


class DocumentAgent(BaseAgent):
    """
    Master Document Intelligence & GraphRAG Agent.

    Orchestrates 12 GraphRAG Phases:
      Phase 1: Multi-Source Document Ingestion
      Phase 2: Structural Document Parsing
      Phase 3: Scanned OCR Processing
      Phase 4: Semantic Hierarchy Chunking
      Phase 5: Metadata Extraction
      Phase 6: Domain Entity Extraction
      Phase 7: Knowledge Graph Linking (DESCRIBES, LOCATED_IN, REFERENCES)
      Phase 8: Async Vector Store Embedding Generation
      Phase 9: Hybrid Retrieval (Graph + Vector)
      Phase 10: Multi-Vector Evidence Reranking
      Phase 11: Prompt Context Building
      Phase 12: Grounded LLM Answer Generation with Auditable Citations.
    """

    name: str = "DocumentAgent"
    version: str = "1.0.0"
    description: str = "Ingests documents into Knowledge Graph + FAISS Vector Store, answering queries with citations."
    capabilities: list[Capability] = [Capability.DOCUMENT_SEARCH, Capability.GRAPH_SEARCH]

    def __init__(self) -> None:
        super().__init__()
        self.embedding_engine = AsyncEmbeddingEngine()
        self.retriever = HybridRetriever()
        self.answer_generator = GroundedAnswerGenerator()

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        query = context.query or "What is the maintenance procedure for Pump P-12?"
        target_doc = context.target_entity_id or "SOP-HS-04.pdf"
        log.info(f"Running GraphRAG Document Intelligence for query: '{query}'")

        # Phase 1: Ingestion
        doc = DocumentIngestionEngine.ingest_document(target_doc, file_type="PDF")

        # Phase 2: Parsing
        parsed_struct = DocumentParser.parse(doc)

        # Phase 4: Semantic Chunking
        raw_chunks = SemanticChunker.chunk_document(doc, parsed_struct)

        # Phase 5: Metadata Extraction
        metadata = MetadataExtractor.extract_metadata(doc)
        doc.metadata = metadata

        # Phase 6: Entity Extraction
        full_text = " ".join([c.content for c in raw_chunks])
        entities = EntityExtractor.extract_entities(full_text)
        doc.extracted_entities = entities

        # Phase 7: Knowledge Graph Linking
        graph_triples = KnowledgeGraphLinker.link_to_graph(doc, entities)

        # Phase 8: Async Embeddings
        chunks = self.embedding_engine.generate_embeddings(raw_chunks)
        doc.chunks = chunks

        # Phase 9: Hybrid Retrieval
        retrieved_chunks, graph_nodes = self.retriever.retrieve_hybrid(query, chunks)

        # Phase 10: Reranking
        reranked_chunks = EvidenceReranker.rerank(query, retrieved_chunks)

        # Phase 11: Prompt Context Builder
        prompt_context = ContextBuilder.build_prompt_context(query, reranked_chunks, graph_nodes, entities)

        # Citations Engine
        citations = CitationEngine.build_citations(reranked_chunks)

        # Phase 12: Grounded Answer Generation
        grounded_answer = self.answer_generator.generate_answer(
            query=query,
            prompt_context=prompt_context,
            chunks=reranked_chunks,
            graph_nodes=graph_nodes,
            citations=citations,
        )

        confidence = DocumentConfidenceEngine.compute_confidence(reranked_chunks)
        explanation = DocumentExplanationGenerator.generate_explanation(grounded_answer)

        # Domain Events
        events = DocumentEventGenerator.generate_events(
            agent_name=self.name,
            doc=doc,
            chunks_count=len(chunks),
            trace_id=context.trace_id,
        )

        recommendations = [f"Refer to {c.doc_title} ({c.section})" for c in citations]

        evidence_items = [
            f"Ingested document '{doc.doc_id}' with {len(chunks)} semantic chunks",
            f"Linked {len(entities)} domain entities to Knowledge Graph ({len(graph_triples)} triples)",
            f"Retrieved {len(reranked_chunks)} reranked chunks and {len(graph_nodes)} graph nodes",
        ]

        return DocumentAgentResult(
            agent_name=self.name,
            success=True,
            confidence=confidence,
            evidence=evidence_items,
            recommendations=recommendations,
            events=events,
            grounded_answer=grounded_answer,
            ingested_documents=[doc],
            retrieved_chunks=reranked_chunks,
            citations=citations,
            output_data={
                "answer": grounded_answer.answer_text,
                "doc_id": doc.doc_id,
                "retrieved_chunks_count": len(reranked_chunks),
                "citations_count": len(citations),
                "citations": [c.model_dump() for c in citations],
            },
            explanation=explanation,
        )
