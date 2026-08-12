from __future__ import annotations
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class HazardKnowledgeGraphSync:
    def __init__(self) -> None:
        self._driver = None
        try:
            from app.infrastructure.neo4j.client import neo4j_driver
            self._driver = neo4j_driver
        except Exception:
            log.warning("Neo4j driver not available for HazardKGSync")
    
    async def sync_propagation_node(self, propagation_id: str, hazard_type: str, source_node_id: str, affected_nodes: dict[str, Any], severity: str) -> bool:
        if not self._driver:
            return False
        try:
            async with self._driver.session() as session:
                await session.run("MERGE (p:HazardPropagation {propagation_id: $prop_id})", prop_id=propagation_id)
                for node_id in affected_nodes:
                    await session.run("MATCH (p:HazardPropagation {propagation_id: $prop_id}), (n {id: $node_id}) MERGE (p)-[:PROPAGATES_TO]->(n)", prop_id=propagation_id, node_id=node_id)
            return True
        except Exception as e:
            log.warning(f"Failed to sync propagation node: {e}")
            return False

    async def sync_exposure_node(self, assessment_id: str, propagation_id: str, exposure_zones: list[dict[str, Any]]) -> bool:
        if not self._driver:
            return False
        try:
            async with self._driver.session() as session:
                await session.run("MERGE (e:ExposureAssessment {assessment_id: $ass_id, propagation_id: $prop_id})", ass_id=assessment_id, prop_id=propagation_id)
                for zone in exposure_zones:
                    await session.run("MATCH (e:ExposureAssessment {assessment_id: $ass_id}), (z:Zone {id: $zone_id}) MERGE (e)-[:EXPOSES]->(z)", ass_id=assessment_id, zone_id=zone.get("zone_id"))
            return True
        except Exception as e:
            log.warning(f"Failed to sync exposure node: {e}")
            return False

    async def sync_containment_node(self, plan_id: str, propagation_id: str, barriers: list[str], shutdown_equipment: list[str]) -> bool:
        if not self._driver:
            return False
        try:
            async with self._driver.session() as session:
                await session.run("MERGE (c:ContainmentPlan {plan_id: $plan_id, propagation_id: $prop_id})", plan_id=plan_id, prop_id=propagation_id)
                for equip in shutdown_equipment:
                    await session.run("MATCH (c:ContainmentPlan {plan_id: $plan_id}), (eq:Equipment {id: $equip}) MERGE (eq)-[:CONTAINED_BY]->(c)", plan_id=plan_id, equip=equip)
            return True
        except Exception as e:
            log.warning(f"Failed to sync containment node: {e}")
            return False

    async def sync_evacuation_node(self, recommendation_id: str, propagation_id: str, safe_zones: list[str], assembly_points: list[str]) -> bool:
        if not self._driver:
            return False
        try:
            async with self._driver.session() as session:
                await session.run("MERGE (e:EvacuationPlan {recommendation_id: $rec_id, propagation_id: $prop_id})", rec_id=recommendation_id, prop_id=propagation_id)
            return True
        except Exception as e:
            log.warning(f"Failed to sync evacuation node: {e}")
            return False

    async def sync_cascade_node(self, cascade_id: str, propagation_id: str, chain_data: dict[str, Any]) -> bool:
        if not self._driver:
            return False
        try:
            async with self._driver.session() as session:
                await session.run("MERGE (c:CascadeFailure {cascade_id: $cas_id, propagation_id: $prop_id})", cas_id=cascade_id, prop_id=propagation_id)
            return True
        except Exception as e:
            log.warning(f"Failed to sync cascade node: {e}")
            return False

    async def sync_critical_asset(self, asset_id: str, criticality_score: float, failure_impact_score: float) -> bool:
        if not self._driver:
            return False
        try:
            async with self._driver.session() as session:
                await session.run("MATCH (a {id: $asset_id}) SET a.criticality_score = $cs, a.failure_impact_score = $fis", asset_id=asset_id, cs=criticality_score, fis=failure_impact_score)
            return True
        except Exception as e:
            log.warning(f"Failed to sync critical asset: {e}")
            return False
