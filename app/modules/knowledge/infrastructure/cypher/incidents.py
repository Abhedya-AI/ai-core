"""Cypher queries for Incident domain operations."""

CREATE_INCIDENT = """
CREATE (i:Incident $properties)
RETURN i
"""

GET_INCIDENT_TIMELINE = """
MATCH (i:Incident {id: $incident_id})
OPTIONAL MATCH (h:Hazard)-[:LEADS_TO|CAUSES]->(i)
OPTIONAL MATCH (i)-[:AFFECTS]->(w:Worker)
OPTIONAL MATCH (i)-[:LOCATED_IN]->(z:Zone)
RETURN i, collect(DISTINCT h) AS hazards, collect(DISTINCT w) AS affected_workers, z
"""

GET_AFFECTED_WORKERS = """
MATCH (i:Incident {id: $incident_id})-[:AFFECTS]->(w:Worker)
RETURN w
"""

GET_INCIDENT_HAZARDS = """
MATCH (h:Hazard)-[:LEADS_TO|CAUSES]->(i:Incident {id: $incident_id})
RETURN h
"""
