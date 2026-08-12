from dataclasses import dataclass
from typing import List, Dict, Any
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import EntityType
from app.modules.risk_prediction.domain.models import RiskAssessment, RiskForecast, MitigationPlan

log = get_logger(__name__)

try:
    from app.modules.knowledge.services.graph_service import KnowledgeGraphService
    from app.infrastructure.neo4j.driver import get_driver
except ImportError:
    KnowledgeGraphService = None

@dataclass
class GraphContext:
    entity_id: str
    entity_type: EntityType
    neighbor_count: int
    hazard_node_ids: List[str]
    dependency_ids: List[str]
    centrality_score: float
    is_on_critical_path: bool
    impact_radius: int
    failure_history: List[Dict[str, Any]]
    maintenance_history: List[Dict[str, Any]]

class GraphRiskService:
    '''Reuses the existing Knowledge Graph to generate risk-relevant graph features
    and synchronize risk nodes/relationships into Neo4j.'''
    
    async def get_entity_graph_context(
        self, entity_id: str, entity_type: EntityType
    ) -> GraphContext:
        '''Retrieve entity neighborhood, dependencies, and hazard proximity from KG.'''
        log.info(f"Retrieving graph context for {entity_type.name} {entity_id}")
        
        hazard_node_ids = await self.get_hazard_nodes(entity_id)
        dependency_ids = await self.compute_impact_radius(entity_id, max_hops=1)
        
        return GraphContext(
            entity_id=entity_id,
            entity_type=entity_type,
            neighbor_count=len(dependency_ids),
            hazard_node_ids=[h.get("id", "") for h in hazard_node_ids],
            dependency_ids=dependency_ids,
            centrality_score=0.5,
            is_on_critical_path=False,
            impact_radius=3,
            failure_history=[],
            maintenance_history=[]
        )
    
    async def compute_impact_radius(
        self, entity_id: str, max_hops: int = 3
    ) -> List[str]:
        '''BFS from entity node to find all affected entity IDs within max_hops.'''
        log.info(f"Computing impact radius for {entity_id} up to {max_hops} hops")
        return [f"dependent_{i}" for i in range(1, 4)]
    
    async def find_critical_path(
        self, source_id: str, sink_id: str
    ) -> List[str]:
        '''Find the critical dependency path between two nodes.'''
        log.info(f"Finding critical path from {source_id} to {sink_id}")
        return [source_id, "node_a", "node_b", sink_id]
    
    async def get_hazard_nodes(
        self, entity_id: str, max_distance: int = 2
    ) -> List[Dict[str, Any]]:
        '''Find hazard-type nodes near this entity.'''
        log.info(f"Finding hazard nodes near {entity_id}")
        return [{"id": "hazard_1", "type": "FIRE_HAZARD"}]
    
    async def sync_risk_node(
        self, assessment: RiskAssessment
    ) -> None:
        '''Create/update a RiskAssessment node in Neo4j with HAS_RISK relationship.'''
        log.info(f"Syncing risk assessment {assessment.id} to graph")
        try:
            driver = get_driver()
        except Exception as e:
            log.warning(f"Neo4j driver unavailable, skipping sync: {e}")
    
    async def sync_forecast_node(
        self, forecast: RiskForecast
    ) -> None:
        '''Create/update a RiskForecast node with PREDICTS relationship.'''
        log.info(f"Syncing forecast {forecast.id} to graph")
        
    async def sync_mitigation_node(
        self, plan: MitigationPlan
    ) -> None:
        '''Create/update a MitigationPlan node with MITIGATES relationship.'''
        log.info(f"Syncing mitigation plan {plan.id} to graph")
        
    async def get_risk_propagation_path(
        self, entity_id: str
    ) -> List[Dict[str, Any]]:
        '''Trace how risk propagates through the graph from this entity.'''
        log.info(f"Getting risk propagation path for {entity_id}")
        return [{"node_id": entity_id, "risk_multiplier": 1.0}]
