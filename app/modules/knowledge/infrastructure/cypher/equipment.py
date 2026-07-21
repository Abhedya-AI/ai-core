"""Cypher queries for Equipment domain operations."""

CREATE_EQUIPMENT = """
MERGE (e:Equipment {code: $code})
SET e += $properties, e.id = $id
RETURN e
"""

EQUIPMENT_IN_ZONE = """
MATCH (e:Equipment)-[:LOCATED_IN]->(z:Zone {id: $zone_id})
RETURN e
"""

ATTACH_SENSOR_TO_EQUIPMENT = """
MATCH (e:Equipment {id: $equipment_id})
MATCH (s:Sensor {id: $sensor_id})
MERGE (e)-[r:HAS_SENSOR]->(s)
RETURN e, s
"""

GET_EQUIPMENT_MAINTENANCE_HISTORY = """
MATCH (m:Maintenance)-[:AFFECTS|ASSIGNED_TO]->(e:Equipment {id: $equipment_id})
RETURN m ORDER BY m.scheduled_date DESC
"""
