"""Cypher queries for Worker domain operations."""

CREATE_WORKER = """
MERGE (w:Worker {badge_number: $badge_number})
SET w += $properties, w.id = $id
RETURN w
"""

UPDATE_WORKER = """
MATCH (w:Worker {id: $id})
SET w += $properties, w.updated_at = $updated_at
RETURN w
"""

GET_WORKER_BY_BADGE = """
MATCH (w:Worker {badge_number: $badge_number})
RETURN w
"""

WORKERS_IN_ZONE = """
MATCH (w:Worker)-[:WORKS_IN]->(z:Zone {id: $zone_id})
RETURN w
"""

ASSIGN_WORKER_ZONE = """
MATCH (w:Worker {id: $worker_id})
MATCH (z:Zone {id: $zone_id})
MERGE (w)-[r:WORKS_IN]->(z)
SET r.assigned_at = $timestamp
RETURN w, z
"""
