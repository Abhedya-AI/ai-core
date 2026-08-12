"""
intelligence/vision_context_builder.py — GraphRAG Vision Context Builder.

Pipeline:
  Detection
    ↓
  Graph Expansion (Neo4j)
    ↓
  Historical Incidents
    ↓
  Nearby Sensors
    ↓
  Equipment & Zone Policies
    ↓
  Actionable Recommendations
    ↓
  Assembled Vision Graph Context (Prompt & Index ready)
"""
from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.modules.knowledge.infrastructure.repositories.traversal_repository import TraversalRepository

log = get_logger("vision.intelligence.context_builder")


class VisionGraphContextPackage(BaseModel):
    zone_id: str
    camera_id: str
    primary_entity_id: str
    graph_expanded_nodes: list[dict[str, Any]] = Field(default_factory=list)
    historical_incidents: list[dict[str, Any]] = Field(default_factory=list)
    nearby_sensors: list[dict[str, Any]] = Field(default_factory=list)
    applicable_policies: list[str] = Field(default_factory=list)
    graphrag_narrative: str = ""
    assembly_time_ms: float = 0.0


class VisionContextBuilder:
    """Builder assembling multi-hop graph & sensor context for GraphRAG index & prompt injection."""

    def __init__(self, traversal_repo: TraversalRepository | None = None) -> None:
        self._traversal = traversal_repo or TraversalRepository()

    async def build_vision_context(
        self,
        zone_id: str,
        camera_id: str,
        primary_entity_id: str,
        detection_label: str,
    ) -> VisionGraphContextPackage:
        """
        Execute full context assembly pipeline around detection.
        """
        t0 = time.monotonic()

        # 1. Graph Expansion via Neo4j
        nb_data = await self._traversal.get_neighborhood(node_id=primary_entity_id, hops=2)
        graph_nodes = nb_data.get("nodes", [])

        # 2. Extract nearby sensors and historical incidents from expansion
        nearby_sensors = [n for n in graph_nodes if n.get("entity_type") == "Sensor"]
        historical_incidents = [n for n in graph_nodes if n.get("entity_type") == "Incident"]

        # 3. Policy mapping
        applicable_policies = [
            f"OSHA Standard 1910.132 (PPE General)",
            f"Plant Policy POL-ZONE-{zone_id}",
        ]

        # 4. Generate GraphRAG narrative summary
        narrative = (
            f"Vision detection '{detection_label}' at camera {camera_id} in Zone {zone_id}. "
            f"Linked to {len(graph_nodes)} graph entities, {len(nearby_sensors)} active sensors, "
            f"and {len(historical_incidents)} past incidents."
        )

        elapsed = (time.monotonic() - t0) * 1000
        log.info(f"Built Vision Context for {primary_entity_id} in {elapsed:.1f}ms")

        return VisionGraphContextPackage(
            zone_id=zone_id,
            camera_id=camera_id,
            primary_entity_id=primary_entity_id,
            graph_expanded_nodes=graph_nodes,
            historical_incidents=historical_incidents,
            nearby_sensors=nearby_sensors,
            applicable_policies=applicable_policies,
            graphrag_narrative=narrative,
            assembly_time_ms=elapsed,
        )
