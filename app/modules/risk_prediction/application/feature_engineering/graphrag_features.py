import uuid
from datetime import datetime, timezone
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import FeatureCategory, EntityType
from app.modules.risk_prediction.domain.models import RiskFeature

try:
    from app.modules.graphrag.services import GraphRAGService
except ImportError:
    GraphRAGService = None

log = get_logger(__name__)

class GraphRAGFeatureExtractor:
    """Extracts semantic and historical features using GraphRAG."""
    
    async def extract(self, entity_id: str, entity_type: EntityType, context: str = '') -> list[RiskFeature]:
        features = []
        now_iso = datetime.now(timezone.utc).isoformat()
        
        has_data = False
        names = [
            "graphrag_historical_similarity",
            "graphrag_incident_frequency",
            "graphrag_root_cause_recurrence",
            "graphrag_maintenance_compliance",
            "graphrag_regulation_violation_risk",
            "graphrag_similar_failure_count",
            "graphrag_recommendation_count",
            "graphrag_context_relevance"
        ]
        
        for name in names:
            features.append(RiskFeature(
                id=str(uuid.uuid4()),
                name=name,
                value=0.0,
                category=FeatureCategory.GRAPHRAG,
                timestamp=now_iso,
                is_missing=not has_data
            ))
            
        if not has_data:
            log.warning(f"GraphRAG data unavailable for {entity_type.value} {entity_id}")
            
        return features
