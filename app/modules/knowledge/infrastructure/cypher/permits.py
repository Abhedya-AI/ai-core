"""Cypher queries for Permit domain operations."""

CREATE_PERMIT = """
CREATE (p:Permit $properties)
RETURN p
"""

PERMITS_IN_ZONE = """
MATCH (p:Permit)-[:LOCATED_IN]->(z:Zone {id: $zone_id})
RETURN p
"""

ACTIVE_PERMITS_FOR_WORKER = """
MATCH (w:Worker {id: $worker_id})<-[:ASSIGNED_TO]-(p:Permit {status: 'ACTIVE'})
RETURN p
"""
