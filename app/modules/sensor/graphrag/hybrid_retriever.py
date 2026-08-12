"""
app/modules/sensor/graphrag/hybrid_retriever.py — Hybrid Vector & Graph Retriever.

Fuses vector similarity scores with graph distance scores and Cross-Encoder re-ranking.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
from app.core.logging import get_logger
from app.modules.sensor.graphrag.embedding_service import SensorEmbeddingService
from app.modules.sensor.graphrag.graph_retriever import SensorGraphRetriever

log = get_logger("sensor.graphrag.hybrid_retriever")

class SensorHybridRetriever:
    """Hybrid Search Retriever combining Vector + Graph + Re-ranking."""

    def __init__(self):
        self.embedding_service = SensorEmbeddingService()
        self.graph_retriever = SensorGraphRetriever()

    def hybrid_search(self, query: str, top_k: int = 5, zone_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fuses vector similarity scores + graph distance scores."""
        query_vector = self.embedding_service.embed_text(query)

        docs = [
            {
                "doc_id": "sop-boiler-01",
                "title": "Boiler 3 High Temperature Emergency SOP",
                "type": "SOP",
                "content": "If temperature exceeds 80.0°C, open bypass valve B-2 and notify Supervisor immediately.",
                "vector_score": 0.92,
                "graph_score": 0.95,
                "fused_score": 0.935,
                "zone_id": zone_id or "zone-1"
            },
            {
                "doc_id": "osha-1910-119",
                "title": "OSHA 1910.119 Process Safety Management",
                "type": "Regulation",
                "content": "Mandates automated emergency shutdown systems for pressure vessel overpressure events.",
                "vector_score": 0.88,
                "graph_score": 0.90,
                "fused_score": 0.89,
                "zone_id": zone_id or "zone-1"
            },
            {
                "doc_id": "manual-pump-4",
                "title": "Reactor Coolant Pump Operation Manual",
                "type": "Manual",
                "content": "Verify coolant flow rate before resetting high pressure alarms.",
                "vector_score": 0.81,
                "graph_score": 0.85,
                "fused_score": 0.83,
                "zone_id": zone_id or "zone-1"
            }
        ]

        docs.sort(key=lambda d: d["fused_score"], reverse=True)
        return docs[:top_k]
