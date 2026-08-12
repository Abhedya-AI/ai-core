import uuid
from datetime import datetime, timezone
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import FeatureCategory, EntityType
from app.modules.risk_prediction.domain.models import RiskFeature

try:
    from app.modules.knowledge.services.graph_service import KnowledgeGraphService
except ImportError:
    KnowledgeGraphService = None

log = get_logger(__name__)

class GraphFeatureExtractor:
    """Extracts topological and structural features from the knowledge graph."""
    
    async def extract(self, entity_id: str, entity_type: EntityType) -> list[RiskFeature]:
        features = []
        now_iso = datetime.now(timezone.utc).isoformat()
        
        has_data = False
        names = [
            "graph_degree_centrality",
            "graph_betweenness_proxy",
            "graph_hazard_proximity",
            "graph_dependency_score",
            "graph_critical_path_score",
            "graph_impact_radius",
            "graph_equipment_connectivity",
            "graph_historical_failure_count",
            "graph_maintenance_gap_days",
            "graph_risk_propagation_score"
        ]
        
        for name in names:
            features.append(RiskFeature(
                id=str(uuid.uuid4()),
                name=name,
                value=0.0,
                category=FeatureCategory.GRAPH,
                timestamp=now_iso,
                is_missing=not has_data
            ))
            
        if not has_data:
            log.warning(f"Graph data unavailable for {entity_type.value} {entity_id}")
            
        return features
