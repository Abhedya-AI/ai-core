"""Cypher queries for Regulation domain operations."""

CREATE_REGULATION = """
MERGE (r:Regulation {code: $code})
SET r += $properties, r.id = $id
RETURN r
"""

REGULATIONS_FOR_HAZARD = """
MATCH (h:Hazard {id: $hazard_id})-[:REFERENCES|COMPLIES_WITH]->(r:Regulation)
RETURN r
"""
