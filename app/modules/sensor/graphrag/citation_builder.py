"""
app/modules/sensor/graphrag/citation_builder.py — Citation Builder.

Formats exact citations for SOPs, OSHA regulations, equipment manuals, and historical incident records.
"""
from __future__ import annotations
from typing import Dict, List, Any
from app.core.logging import get_logger

log = get_logger("sensor.graphrag.citation_builder")

class SensorCitationBuilder:
    """Formats structured citations for retrieved evidence."""

    def build_citations(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations = []
        for i, doc in enumerate(retrieved_docs, start=1):
            citations.append({
                "citation_id": f"CIT-{i:03d}",
                "doc_id": doc.get("doc_id", f"doc-{i}"),
                "title": doc.get("title", "Industrial Guidance"),
                "type": doc.get("type", "Standard"),
                "snippet": doc.get("content", "")[:150] + "...",
                "relevance_score": doc.get("fused_score", 0.90)
            })
        return citations
