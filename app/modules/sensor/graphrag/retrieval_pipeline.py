"""
app/modules/sensor/graphrag/retrieval_pipeline.py — GraphRAG Retrieval Pipeline.

Executes end-to-end GraphRAG pipeline:
  Query Expander → Vector/Graph Retrievers → Hybrid Fusion → Citation Builder.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
from app.core.logging import get_logger
from app.modules.sensor.graphrag.query_expander import SensorQueryExpander
from app.modules.sensor.graphrag.graph_retriever import SensorGraphRetriever
from app.modules.sensor.graphrag.hybrid_retriever import SensorHybridRetriever
from app.modules.sensor.graphrag.citation_builder import SensorCitationBuilder

log = get_logger("sensor.graphrag.pipeline")

class SensorGraphRAGPipeline:
    """Coordinates the full GraphRAG execution pipeline."""

    def __init__(self):
        self.expander = SensorQueryExpander()
        self.graph_retriever = SensorGraphRetriever()
        self.hybrid_retriever = SensorHybridRetriever()
        self.citation_builder = SensorCitationBuilder()

    def execute_pipeline(self, query: str, sensor_id: Optional[str] = None, zone_id: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """Execute full GraphRAG retrieval pipeline."""
        expanded = self.expander.expand_query(query, sensor_id=sensor_id, zone_id=zone_id)
        graph_ctx = self.graph_retriever.retrieve_graph_context(sensor_id or "s1")
        hybrid_docs = self.hybrid_retriever.hybrid_search(query, top_k=top_k, zone_id=zone_id)
        citations = self.citation_builder.build_citations(hybrid_docs)

        evidence_text = "\n".join([f"- [{c['citation_id']}] {c['title']}: {c['snippet']}" for c in citations])

        return {
            "query": query,
            "expanded_query": expanded,
            "graph_context": graph_ctx,
            "retrieved_documents": hybrid_docs,
            "citations": citations,
            "fused_evidence_text": evidence_text
        }
