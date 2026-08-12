"""
intelligence/risk_context_builder.py — Multi-Source Risk Context Builder.

Fuses multi-source context (Knowledge Graph, Sensor Intelligence, historical incidents)
into a unified VisionRiskContext object used by vision intelligence engines.
"""
from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.knowledge.infrastructure.repositories.traversal_repository import TraversalRepository

log = get_logger("vision.intelligence.risk_context")


class VisionRiskContext(BaseModel):
    zone_id: str
    camera_id: str
    zone_risk_level: str = "LOW"
    active_sensor_alerts: list[dict[str, Any]] = Field(default_factory=list)
    nearby_equipment_types: list[str] = Field(default_factory=list)
    zone_worker_count: int = 0
    historical_incident_count: int = 0
    requires_strict_ppe: bool = False
    context_build_time_ms: float = 0.0


class MultiSourceRiskContextBuilder:
    """Builder gathering multi-source context across KG, sensors, and historical logs."""

    def __init__(
        self,
        base_repo: BaseNeo4jRepository | None = None,
        traversal_repo: TraversalRepository | None = None,
    ) -> None:
        self._base = base_repo or BaseNeo4jRepository()
        self._traversal = traversal_repo or TraversalRepository()

    async def build_context(self, zone_id: str, camera_id: str) -> VisionRiskContext:
        """Gather context for zone_id and camera_id."""
        t0 = time.monotonic()

        # Fetch zone node properties from Neo4j
        zone_node = await self._base.find_by_id(zone_id, label="Zone") or {}
        risk_level = zone_node.get("risk_level", zone_node.get("severity", "LOW"))

        # Traversal neighborhood around zone
        nb = await self._traversal.get_neighborhood(node_id=zone_id, hops=1)
        nodes = nb.get("nodes", [])

        equip_types = sorted(list({n.get("equipment_type", "EQUIPMENT") for n in nodes if n.get("entity_type") == "Equipment"}))
        sensor_alerts = [n for n in nodes if n.get("entity_type") == "Alert"]
        incidents = [n for n in nodes if n.get("entity_type") == "Incident"]

        requires_strict_ppe = risk_level in ("HIGH", "CRITICAL") or len(equip_types) > 0

        elapsed = (time.monotonic() - t0) * 1000

        return VisionRiskContext(
            zone_id=zone_id,
            camera_id=camera_id,
            zone_risk_level=risk_level,
            active_sensor_alerts=sensor_alerts,
            nearby_equipment_types=equip_types,
            zone_worker_count=len([n for n in nodes if n.get("entity_type") in ("Worker", "Contractor")]),
            historical_incident_count=len(incidents),
            requires_strict_ppe=requires_strict_ppe,
            context_build_time_ms=elapsed,
        )
