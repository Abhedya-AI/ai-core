from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

log = logging.getLogger(__name__)

class ForecastKnowledgeGraphSync:
    """Synchronizes Forecast data to the Neo4j Knowledge Graph.
    
    Creates/updates Forecast, Scenario, MaintenanceForecast nodes
    and FORECASTS, AFFECTS, LIKELY_TO_CAUSE, REQUIRES, SUPPORTS relationships.
    """
    
    def __init__(self, knowledge_service: Any = None):
        self._knowledge_service = knowledge_service
        self._neo4j_driver = None
    
    async def _get_driver(self) -> Any:
        if self._neo4j_driver:
            return self._neo4j_driver
        try:
            from app.infrastructure.neo4j.driver import get_driver
            self._neo4j_driver = await get_driver()
            return self._neo4j_driver
        except Exception:
            return None
    
    async def sync_forecast_node(self, forecast_id: str, entity_id: str, forecast_type: str, predicted_value: float, confidence: float, horizon: str) -> bool:
        """Create/update a :Forecast node linked to entity with :FORECASTS relationship."""
        driver = await self._get_driver()
        if not driver:
            log.warning("Neo4j unavailable, skipping forecast KG sync")
            return False
            
        cypher = """
        MERGE (f:Forecast {forecast_id: $forecast_id})
        SET f.entity_id = $entity_id,
            f.forecast_type = $forecast_type,
            f.predicted_value = $predicted_value,
            f.confidence = $confidence,
            f.horizon = $horizon,
            f.synced_at = $synced_at
        WITH f
        MATCH (e {id: $entity_id})
        MERGE (e)-[:FORECASTS]->(f)
        RETURN f.forecast_id
        """
        try:
            async with driver.session() as session:
                await session.run(cypher, forecast_id=forecast_id, entity_id=entity_id, forecast_type=forecast_type, predicted_value=predicted_value, confidence=confidence, horizon=horizon, synced_at=datetime.now(timezone.utc).isoformat())
            return True
        except Exception as e:
            log.error(f"Failed to sync forecast node: {e}")
            return False
    
    async def sync_maintenance_forecast(self, equipment_id: str, rul_hours: float, urgency: str, forecast_id: str) -> bool:
        """Create MaintenanceForecast node with REQUIRES relationship."""
        driver = await self._get_driver()
        if not driver:
            return False
        cypher = """
        MERGE (m:MaintenanceForecast {forecast_id: $forecast_id})
        SET m.rul_hours = $rul_hours, m.urgency = $urgency
        WITH m
        MATCH (e:Equipment {id: $equipment_id})
        MERGE (e)-[:REQUIRES]->(m)
        """
        try:
            async with driver.session() as session:
                await session.run(cypher, equipment_id=equipment_id, rul_hours=rul_hours, urgency=urgency, forecast_id=forecast_id)
            return True
        except Exception:
            return False
    
    async def sync_hazard_forecast(self, hazard_id: str, affected_zone_ids: list[str], forecast_id: str, propagation_probability: float) -> bool:
        """Create HazardForecast node with LIKELY_TO_CAUSE and AFFECTS relationships."""
        driver = await self._get_driver()
        if not driver:
            return False
        cypher = """
        MERGE (h:HazardForecast {forecast_id: $forecast_id})
        SET h.propagation_probability = $propagation_probability
        WITH h
        MATCH (hz:Hazard {id: $hazard_id})
        MERGE (hz)-[:LIKELY_TO_CAUSE]->(h)
        WITH h
        UNWIND $affected_zone_ids AS z_id
        MATCH (z:Zone {id: z_id})
        MERGE (h)-[:AFFECTS]->(z)
        """
        try:
            async with driver.session() as session:
                await session.run(cypher, hazard_id=hazard_id, affected_zone_ids=affected_zone_ids, forecast_id=forecast_id, propagation_probability=propagation_probability)
            return True
        except Exception:
            return False
    
    async def sync_scenario_node(self, scenario_id: str, entity_id: str, scenario_type: str, data: dict) -> bool:
        """Create :ForecastScenario node with SUPPORTS relationship."""
        driver = await self._get_driver()
        if not driver:
            return False
        cypher = """
        MERGE (s:ForecastScenario {scenario_id: $scenario_id})
        SET s.scenario_type = $scenario_type
        WITH s
        MATCH (e {id: $entity_id})
        MERGE (s)-[:SUPPORTS]->(e)
        """
        try:
            async with driver.session() as session:
                await session.run(cypher, scenario_id=scenario_id, entity_id=entity_id, scenario_type=scenario_type)
            return True
        except Exception:
            return False
    
    async def create_resource_forecast_relationships(self, resource_forecast_id: str, required_resources: list[str]) -> bool:
        """Create REQUIRES relationships from forecast to resource nodes."""
        driver = await self._get_driver()
        if not driver:
            return False
        cypher = """
        MATCH (f:ResourceForecast {forecast_id: $resource_forecast_id})
        UNWIND $required_resources AS r_id
        MATCH (r:Resource {id: r_id})
        MERGE (f)-[:REQUIRES]->(r)
        """
        try:
            async with driver.session() as session:
                await session.run(cypher, resource_forecast_id=resource_forecast_id, required_resources=required_resources)
            return True
        except Exception:
            return False
