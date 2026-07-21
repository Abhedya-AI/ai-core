"""Cypher queries for Hazard domain operations."""

CREATE_HAZARD = """
CREATE (h:Hazard $properties)
RETURN h
"""

GET_ACTIVE_HAZARDS = """
MATCH (h:Hazard {mitigated: false})
RETURN h ORDER BY h.timestamp DESC
"""

HAZARDS_IN_ZONE = """
MATCH (h:Hazard)-[:LOCATED_IN]->(z:Zone {id: $zone_id})
WHERE h.mitigated = false
RETURN h
"""

CRITICAL_HAZARDS = """
MATCH (h:Hazard {severity: 'CRITICAL', mitigated: false})
RETURN h ORDER BY h.timestamp DESC
"""
