from __future__ import annotations
import uuid
from datetime import datetime, timezone

from app.core.logging import get_logger
log = get_logger(__name__)

try:
    from app.modules.knowledge.services.knowledge_service import KnowledgeService
except ImportError:
    KnowledgeService = None

try:
    from app.modules.graphrag.services.graphrag_service import GraphRAGService
except ImportError:
    GraphRAGService = None

class ForecastRecommendationEngine:
    """Engine for generating actionable recommendations from forecasts."""

    def __init__(self, graphrag_service=None, knowledge_service=None) -> None:
        self.graphrag_service = graphrag_service
        self.knowledge_service = knowledge_service
        self.rec_type_map = {
            "degradation": "MAINTENANCE",
            "gas_accumulation": "SAFETY",
            "temperature": "ENVIRONMENTAL",
            "worker_availability": "RESOURCE",
            "production_impact": "OPERATIONAL"
        }

    async def generate_recommendations(self, forecast_type: str, forecast_value: float, entity_id: str, entity_type: str, context: dict) -> list[dict]:
        """Generate prioritized recommendations based on forecast results."""
        log.info(f"Generating recommendations for {forecast_type} on {entity_id}")
        
        recs = []
        rec_type = self.rec_type_map.get(forecast_type, "GENERAL")
        
        # Rule-based priority
        priority = "LOW"
        if forecast_value > 0.8:
            priority = "IMMEDIATE"
        elif forecast_value > 0.6:
            priority = "URGENT"
        elif forecast_value > 0.4:
            priority = "HIGH"
            
        # Optional GraphRAG enrichment
        graphrag_citations = []
        if self.graphrag_service:
            try:
                query = self._build_recommendation_query(forecast_type, forecast_value, entity_id)
                rag_response = await self.graphrag_service.answer(query)
                if rag_response and hasattr(rag_response, 'citations'):
                    graphrag_citations = rag_response.citations
            except Exception as e:
                log.warning(f"GraphRAG query failed during recommendation generation: {e}")
                
        # Base concrete recommendations (generating at least 2)
        recs.append({
            "recommendation_id": str(uuid.uuid4()),
            "type": rec_type,
            "priority": priority,
            "title": f"Address {forecast_type} risk for {entity_type}",
            "description": f"Forecast indicates a value of {forecast_value:.2f}, requiring attention.",
            "rationale": "Automated threshold rule.",
            "kg_node_refs": [entity_id],
            "graphrag_citations": graphrag_citations,
            "risk_refs": [],
            "rca_refs": [],
            "estimated_impact": "High",
            "time_to_implement": "2 hours",
            "resources_required": ["Technician"],
            "applies_to": [entity_id]
        })
        
        recs.append({
            "recommendation_id": str(uuid.uuid4()),
            "type": "MONITORING",
            "priority": "HIGH" if priority in ["IMMEDIATE", "URGENT"] else "MEDIUM",
            "title": f"Increase monitoring frequency for {entity_id}",
            "description": "Adjust sensor polling or manual inspection frequency.",
            "rationale": "High uncertainty or approaching threshold.",
            "kg_node_refs": [entity_id],
            "graphrag_citations": [],
            "risk_refs": [],
            "rca_refs": [],
            "estimated_impact": "Medium",
            "time_to_implement": "15 mins",
            "resources_required": ["System Config"],
            "applies_to": [entity_id]
        })
        
        return self._prioritize_recommendations(recs, forecast_value)

    def _build_recommendation_query(self, forecast_type: str, forecast_value: float, entity_id: str) -> str:
        """Build natural language query for GraphRAG."""
        return f"What are the standard mitigation procedures for high {forecast_type} risk on equipment {entity_id}?"

    def _prioritize_recommendations(self, recs: list[dict], forecast_value: float) -> list[dict]:
        """Sort recommendations by priority."""
        priority_map = {"IMMEDIATE": 4, "URGENT": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
        return sorted(recs, key=lambda x: priority_map.get(x["priority"], 0), reverse=True)
