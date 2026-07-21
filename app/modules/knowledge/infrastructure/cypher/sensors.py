"""Cypher queries for Sensor domain operations."""

CREATE_SENSOR = """
MERGE (s:Sensor {id: $id})
SET s += $properties
RETURN s
"""

SENSORS_FOR_EQUIPMENT = """
MATCH (e:Equipment {id: $equipment_id})-[:HAS_SENSOR]->(s:Sensor)
RETURN s
"""

SENSORS_IN_ZONE = """
MATCH (s:Sensor)-[:LOCATED_IN]->(z:Zone {id: $zone_id})
RETURN s
"""
