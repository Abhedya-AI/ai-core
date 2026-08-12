"""investigation_context_builder.py — Aggregates all platform context for an investigation.

Merges:
  - Sensor Intelligence: recent readings for relevant sensors
  - Vision Intelligence: recent detections for relevant cameras
  - Knowledge Graph: entity subgraph (zone, equipment, workers, hazards)
  - GraphRAG: relevant SOPs, policies, regulations
  - Historical incidents: similar past investigations from memory
  - Maintenance records from Knowledge Graph
  - Supervisor decisions

Output: InvestigationContext — reusable structured input for reasoning engines.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.root_cause.domain.models import (
    Investigation, InvestigationContext,
)

log = get_logger("root_cause.context.builder")

# Neo4j queries for context aggregation
_ZONE_ENTITIES = """
MATCH (z:Zone {id: $zone_id})-[r]-(e)
RETURN type(r) AS rel, labels(e) AS entity_labels,
       e.id AS entity_id, e.name AS entity_name, e.status AS status
LIMIT 30
"""

_EQUIPMENT_HEALTH = """
MATCH (eq:Equipment)
WHERE eq.id IN $equipment_ids
RETURN eq.id AS id, eq.name AS name, eq.status AS status,
       eq.last_maintenance AS last_maintenance, eq.health_score AS health_score
"""

_WORKERS_IN_ZONE = """
MATCH (w:Worker)-[:LOCATED_IN|:WORKS_IN|:ASSIGNED_TO]->(z:Zone {id: $zone_id})
RETURN w.id AS id, w.name AS name, w.role AS role
LIMIT 20
"""

_ACTIVE_HAZARDS = """
MATCH (h:Hazard)-[:LOCATED_IN|:AFFECTS]->(z:Zone {id: $zone_id})
WHERE h.status IN ['ACTIVE', 'MONITORING']
RETURN h.id AS id, h.name AS name, h.severity AS severity, h.description AS description
LIMIT 10
"""

_APPLICABLE_POLICIES = """
MATCH (p:Policy)-[:APPLIES_TO]->(z:Zone {id: $zone_id})
RETURN p.name AS name, p.description AS description, p.code AS code
LIMIT 10
"""

_APPLICABLE_REGULATIONS = """
MATCH (r:Regulation)-[:GOVERNS|:APPLIES_TO]->(z:Zone)
WHERE z.id = $zone_id
RETURN r.name AS name, r.code AS code
LIMIT 10
"""

_MAINTENANCE_HISTORY = """
MATCH (m:Maintenance)-[:PERFORMED_ON]->(eq:Equipment)
WHERE eq.id IN $equipment_ids
RETURN eq.id AS equipment_id, eq.name AS equipment_name,
       m.performed_at AS performed_at, m.type AS maintenance_type,
       m.status AS status
ORDER BY m.performed_at DESC
LIMIT 20
"""


class InvestigationContextBuilder:
    """Builds a complete InvestigationContext from all platform data sources."""

    def __init__(self, repo: BaseNeo4jRepository | None = None) -> None:
        self._repo = repo or BaseNeo4jRepository()

    async def build(
        self,
        investigation: Investigation,
        sensor_readings: list[dict[str, Any]] | None = None,
        vision_detections: list[dict[str, Any]] | None = None,
        similar_incidents: list[str] | None = None,
    ) -> InvestigationContext:
        """Build the full investigation context by querying all data sources."""
        log.info(f"Building context for investigation {investigation.id}")
        zone_id = investigation.zone_id
        equipment_ids = investigation.equipment_ids

        # Knowledge Graph queries (all non-fatal — return empty list on failure)
        kg_entities = await self._get_zone_entities(zone_id) if zone_id else []
        equipment_health = await self._get_equipment_health(equipment_ids) if equipment_ids else {}
        maintenance_records = await self._get_maintenance_records(equipment_ids) if equipment_ids else []
        active_policies = await self._get_policies(zone_id) if zone_id else []
        applicable_regs = await self._get_regulations(zone_id) if zone_id else []
        kg_relationships = await self._get_relationship_summary(zone_id) if zone_id else []

        # Completeness score — fraction of context components populated
        components = [
            bool(sensor_readings),
            bool(vision_detections),
            bool(kg_entities),
            bool(maintenance_records),
            bool(active_policies),
            bool(similar_incidents),
        ]
        completeness = sum(1 for c in components if c) / len(components)

        context = InvestigationContext(
            investigation_id=investigation.id,
            incident_id=investigation.incident_id,
            sensor_readings_summary=sensor_readings or [],
            vision_detections_summary=vision_detections or [],
            kg_entities=kg_entities,
            kg_relationships=kg_relationships,
            rag_documents=[],  # Populated by GraphRAG integration downstream
            similar_incidents=similar_incidents or [],
            maintenance_records=maintenance_records,
            active_policies=[p.get("name", "") for p in active_policies if p.get("name")],
            applicable_regulations=[r.get("name", "") for r in applicable_regs if r.get("name")],
            supervisor_decisions=[],  # Populated by Supervisor module
            historical_recommendations=[],
            zone_risk_level=self._infer_zone_risk(kg_entities),
            equipment_health_summary=equipment_health,
            context_completeness_score=round(completeness, 2),
        )
        log.info(f"Context built for {investigation.id}: completeness={completeness:.0%}")
        return context

    async def _get_zone_entities(self, zone_id: str) -> list[dict[str, Any]]:
        try:
            records = await self._repo.execute_query(_ZONE_ENTITIES, {"zone_id": zone_id})
            return [{"rel": r.get("rel"), "entity_id": r.get("entity_id"),
                     "entity_name": r.get("entity_name"), "labels": r.get("entity_labels"),
                     "status": r.get("status")} for r in records]
        except Exception as exc:
            log.warning(f"Zone entities query failed: {exc}")
            return []

    async def _get_equipment_health(self, equipment_ids: list[str]) -> dict[str, Any]:
        try:
            records = await self._repo.execute_query(_EQUIPMENT_HEALTH, {"equipment_ids": equipment_ids})
            return {
                r.get("id", "unknown"): {
                    "name": r.get("name"), "status": r.get("status"),
                    "last_maintenance": r.get("last_maintenance"),
                    "health_score": r.get("health_score"),
                }
                for r in records
            }
        except Exception as exc:
            log.warning(f"Equipment health query failed: {exc}")
            return {}

    async def _get_maintenance_records(self, equipment_ids: list[str]) -> list[dict[str, Any]]:
        try:
            records = await self._repo.execute_query(_MAINTENANCE_HISTORY, {"equipment_ids": equipment_ids})
            return [
                {"equipment_id": r.get("equipment_id"), "equipment_name": r.get("equipment_name"),
                 "performed_at": r.get("performed_at"), "type": r.get("maintenance_type"),
                 "status": r.get("status")}
                for r in records
            ]
        except Exception as exc:
            log.warning(f"Maintenance records query failed: {exc}")
            return []

    async def _get_policies(self, zone_id: str) -> list[dict[str, Any]]:
        try:
            return await self._repo.execute_query(_APPLICABLE_POLICIES, {"zone_id": zone_id})
        except Exception as exc:
            log.warning(f"Policies query failed: {exc}")
            return []

    async def _get_regulations(self, zone_id: str) -> list[dict[str, Any]]:
        try:
            return await self._repo.execute_query(_APPLICABLE_REGULATIONS, {"zone_id": zone_id})
        except Exception as exc:
            log.warning(f"Regulations query failed: {exc}")
            return []

    async def _get_relationship_summary(self, zone_id: str) -> list[dict[str, Any]]:
        try:
            query = """
            MATCH (z:Zone {id: $zone_id})-[r]-(e)
            RETURN type(r) AS rel_type, count(e) AS count
            LIMIT 20
            """
            return await self._repo.execute_query(query, {"zone_id": zone_id})
        except Exception as exc:
            log.warning(f"Relationship summary query failed: {exc}")
            return []

    @staticmethod
    def _infer_zone_risk(entities: list[dict[str, Any]]) -> str:
        """Infer zone risk level from entity statuses."""
        statuses = [e.get("status", "") for e in entities if e.get("status")]
        if any(s in ("CRITICAL", "EMERGENCY", "FAULT") for s in statuses):
            return "CRITICAL"
        if any(s in ("WARNING", "HIGH", "DEGRADED") for s in statuses):
            return "HIGH"
        if any(s in ("MAINTENANCE", "MEDIUM") for s in statuses):
            return "MEDIUM"
        return "LOW"
