"""
app/modules/sensor/graphrag/query_expander.py — Natural Language Query Expander.

Expands sensor queries into spatial, temporal, equipment, hazard, and regulatory search terms.
"""
from __future__ import annotations
from typing import Dict, List, Optional
from app.core.logging import get_logger

log = get_logger("sensor.graphrag.query_expander")

class SensorQueryExpander:
    """Expands queries for GraphRAG search."""

    def expand_query(self, query: str, sensor_id: Optional[str] = None, zone_id: Optional[str] = None) -> Dict[str, Any]:
        q_lower = query.lower()
        expanded_terms = [q_lower]

        spatial_terms = []
        if "zone" in q_lower or zone_id:
            spatial_terms.append(zone_id or "zone-1")
            spatial_terms.append("boiler_room")

        equipment_terms = []
        if "boiler" in q_lower or "pump" in q_lower:
            equipment_terms.extend(["boiler_3", "reactor_pump", "pressure_vessel"])

        hazard_terms = []
        if "temperature" in q_lower or "heat" in q_lower:
            hazard_terms.extend(["overtemperature", "thermal_runaway", "fire_hazard"])
        if "pressure" in q_lower:
            hazard_terms.extend(["overpressure", "burst_risk", "pipe_rupture"])

        regulatory_terms = ["OSHA 1910.119 PSM", "NFPA 85 Boiler Standard", "ISO 45001"]

        return {
            "original_query": query,
            "sensor_id": sensor_id,
            "zone_id": zone_id,
            "expanded_terms": expanded_terms,
            "spatial_terms": spatial_terms,
            "equipment_terms": equipment_terms,
            "hazard_terms": hazard_terms,
            "regulatory_terms": regulatory_terms
        }
