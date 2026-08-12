from typing import Any
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.models import RiskAssessment, RiskForecast, MitigationPlan

log = get_logger(__name__)

try:
    from app.infrastructure.neo4j.driver import get_driver
except ImportError:
    def get_driver(): return None

class Neo4jRiskRepository:
    """Synchronizes risk assessment data into Neo4j Knowledge Graph.
    Creates and maintains RiskAssessment nodes and relationships.
    """
    
    def __init__(self):
        self.driver = get_driver()
        
    async def upsert_risk_node(self, assessment: RiskAssessment) -> None:
        """MERGE risk node, set properties, create HAS_RISK relationship."""
        if not self.driver:
            return
            
        max_pred = max(assessment.predictions, key=lambda p: p.score.probability, default=None)
        risk_val = max_pred.score.probability if max_pred else 0.0
        risk_lvl = max_pred.score.level.value if hasattr(max_pred.score, 'level') else "UNKNOWN"

        query = """
        MERGE (a:RiskAssessment {id: $assessment_id})
        SET a.timestamp = $timestamp,
            a.status = $status,
            a.level = $level,
            a.value = $value
        WITH a
        MATCH (e) WHERE e.id = $entity_id
        MERGE (e)-[:HAS_RISK]->(a)
        """
        try:
            async with self.driver.session() as session:
                await session.run(
                    query, 
                    assessment_id=assessment.id,
                    timestamp=assessment.timestamp,
                    status=assessment.status.value,
                    level=risk_lvl,
                    value=risk_val,
                    entity_id=assessment.entity_id
                )
        except Exception as e:
            log.error(f"Failed to upsert risk node for {assessment.id}: {e}")
            
    async def upsert_forecast_node(self, forecast: RiskForecast) -> None:
        """MERGE forecast node, create PREDICTS relationship."""
        if not self.driver:
            return
            
        query = """
        MERGE (f:RiskForecast {id: $forecast_id})
        SET f.generated_at = $generated_at
        WITH f
        MATCH (e) WHERE e.id = $entity_id
        MERGE (e)-[:HAS_FORECAST]->(f)
        """
        try:
            async with self.driver.session() as session:
                await session.run(
                    query, 
                    forecast_id=forecast.id,
                    generated_at=getattr(forecast, "generated_at", "unknown"),
                    entity_id=getattr(forecast, "entity_id", "unknown")
                )
        except Exception as e:
            log.error(f"Failed to upsert forecast node for {forecast.id}: {e}")
            
    async def upsert_mitigation_node(self, plan: MitigationPlan) -> None:
        """MERGE mitigation node, create MITIGATES relationship."""
        if not self.driver:
            return
            
        query = """
        MERGE (m:MitigationPlan {id: $plan_id})
        SET m.priority = $priority
        WITH m
        MATCH (a:RiskAssessment {id: $assessment_id})
        MERGE (m)-[:MITIGATES]->(a)
        """
        try:
            async with self.driver.session() as session:
                await session.run(
                    query, 
                    plan_id=plan.id,
                    priority=plan.priority.value if hasattr(plan, 'priority') else "UNKNOWN",
                    assessment_id=getattr(plan, "assessment_id", "unknown")
                )
        except Exception as e:
            log.error(f"Failed to upsert mitigation node for {plan.id}: {e}")
            
    async def get_entity_risk_subgraph(
        self, entity_id: str, depth: int = 2
    ) -> list[dict]:
        """Retrieve risk subgraph for entity (nodes + relationships)."""
        if not self.driver:
            return []
            
        query = f"""
        MATCH path = (e {{id: $entity_id}})-[*1..{depth}]-(n)
        WHERE n:RiskAssessment OR n:RiskForecast OR n:MitigationPlan
        RETURN path
        """
        try:
            async with self.driver.session() as session:
                result = await session.run(query, entity_id=entity_id)
                return [record["path"] async for record in result]
        except Exception as e:
            log.error(f"Failed to get subgraph for {entity_id}: {e}")
            return []
            
    async def find_escalation_path(
        self, from_entity_id: str
    ) -> list[dict]:
        """Trace ESCALATES_TO path from this entity."""
        if not self.driver:
            return []
            
        query = """
        MATCH path = (e {{id: $from_entity_id}})-[:ESCALATES_TO*]->(n)
        RETURN path
        """
        try:
            async with self.driver.session() as session:
                result = await session.run(query, from_entity_id=from_entity_id)
                return [record["path"] async for record in result]
        except Exception as e:
            log.error(f"Failed to find escalation path for {from_entity_id}: {e}")
            return []
