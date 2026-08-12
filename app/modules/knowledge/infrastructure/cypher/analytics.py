"""
cypher/analytics.py — Analytics and Aggregation Cypher Query Constants.

Aggregation queries for dashboards, reports, and KPI computations.
All parameterized with $param syntax.
"""

# ── Subgraph Statistics ────────────────────────────────────────────────────────

SUBGRAPH_NODE_COUNT_BY_LABEL = """
MATCH (n)
RETURN labels(n)[0] AS label, count(n) AS count
ORDER BY count DESC
"""

SUBGRAPH_RELATIONSHIP_COUNT_BY_TYPE = """
MATCH ()-[r]->()
RETURN type(r) AS rel_type, count(r) AS count
ORDER BY count DESC
"""

TOTAL_GRAPH_STATS = """
MATCH (n)
WITH count(n) AS total_nodes
MATCH ()-[r]->()
WITH total_nodes, count(r) AS total_relationships
MATCH (n)
WITH total_nodes, total_relationships, collect(DISTINCT labels(n)[0]) AS label_list
RETURN total_nodes, total_relationships, size(label_list) AS unique_labels
"""

# ── Risk & Hazard Distribution ─────────────────────────────────────────────────

RISK_DISTRIBUTION_BY_LEVEL = """
MATCH (n)
WHERE n.risk_level IS NOT NULL
RETURN n.entity_type AS entity_type,
       n.risk_level AS risk_level,
       count(n) AS count
ORDER BY n.entity_type, n.risk_level
"""

SEVERITY_DISTRIBUTION = """
MATCH (n)
WHERE n.severity IS NOT NULL
RETURN n.entity_type AS entity_type,
       n.severity AS severity,
       count(n) AS count
ORDER BY n.entity_type, n.severity
"""

HAZARD_FREQUENCY_BY_TYPE = """
MATCH (h:Hazard)
RETURN coalesce(h.hazard_type, h.entity_type) AS hazard_type,
       count(h) AS frequency,
       collect(h.id)[0..5] AS sample_ids
ORDER BY frequency DESC
LIMIT $limit
"""

HIGH_RISK_SUBGRAPH = """
MATCH (n)
WHERE n.risk_level IN ['HIGH', 'CRITICAL'] OR n.severity IN ['HIGH', 'CRITICAL', 'EMERGENCY']
OPTIONAL MATCH (n)-[r]-(neighbor)
RETURN n,
       n.entity_type AS label,
       n.name AS name,
       n.risk_level AS risk_level,
       n.severity AS severity,
       collect(DISTINCT {id: neighbor.id, type: neighbor.entity_type, rel: type(r)}) AS connections
LIMIT $limit
"""

# ── Incident Analytics ────────────────────────────────────────────────────────

INCIDENT_TIMELINE = """
MATCH (i:Incident)
OPTIONAL MATCH (i)-[:AFFECTS|LOCATED_IN]->(z)
WHERE z.entity_type IN ['Zone', 'Building', 'Floor']
RETURN i.id AS incident_id,
       i.title AS title,
       i.status AS status,
       i.severity AS severity,
       i.timestamp AS timestamp,
       collect(DISTINCT z.name) AS affected_zones
ORDER BY i.timestamp DESC
LIMIT $limit
"""

INCIDENT_STATUS_SUMMARY = """
MATCH (i:Incident)
RETURN i.status AS status, count(i) AS count
ORDER BY count DESC
"""

OPEN_INCIDENTS_WITH_CONTEXT = """
MATCH (i:Incident)
WHERE i.status IN ['OPEN', 'INVESTIGATING', 'IN_PROGRESS']
OPTIONAL MATCH (i)<-[:LEADS_TO|CAUSES]-(h:Hazard)
OPTIONAL MATCH (i)-[:AFFECTS]->(w)
WHERE w.entity_type IN ['Worker', 'Contractor']
RETURN i,
       collect(DISTINCT h.title) AS hazard_causes,
       count(DISTINCT w) AS affected_workers
ORDER BY i.timestamp DESC
LIMIT $limit
"""

# ── Equipment Analytics ───────────────────────────────────────────────────────

EQUIPMENT_STATUS_SUMMARY = """
MATCH (e:Equipment)
RETURN e.status AS status, count(e) AS count
ORDER BY count DESC
"""

EQUIPMENT_AT_RISK = """
MATCH (e:Equipment)-[:HAS_RISK]->(h)
WHERE h.severity IN ['HIGH', 'CRITICAL'] OR h.risk_level IN ['HIGH', 'CRITICAL']
RETURN e.id AS equipment_id,
       e.name AS name,
       e.code AS code,
       e.status AS status,
       count(h) AS hazard_count,
       collect(h.title) AS hazard_titles
ORDER BY hazard_count DESC
LIMIT $limit
"""

MAINTENANCE_OVERDUE = """
MATCH (e:Equipment)
WHERE e.next_maintenance_date IS NOT NULL
AND e.next_maintenance_date < $current_date
AND e.status <> 'DECOMMISSIONED'
RETURN e.id AS equipment_id,
       e.name AS name,
       e.code AS code,
       e.next_maintenance_date AS due_date,
       e.status AS status
ORDER BY e.next_maintenance_date
LIMIT $limit
"""

# ── Sensor Analytics ──────────────────────────────────────────────────────────

SENSOR_STATUS_SUMMARY = """
MATCH (s:Sensor)
RETURN s.sensor_type AS sensor_type,
       s.status AS status,
       count(s) AS count
ORDER BY s.sensor_type, s.status
"""

SENSORS_BY_ZONE = """
MATCH (s:Sensor)-[:MONITORS|LOCATED_IN]->(target)
RETURN target.id AS zone_id,
       target.name AS zone_name,
       target.entity_type AS zone_type,
       count(s) AS sensor_count,
       collect(s.sensor_type) AS sensor_types
ORDER BY sensor_count DESC
"""

LATEST_READING_PER_SENSOR = """
MATCH (s:Sensor)-[:GENERATED|HAS_READING]->(r:Reading)
WITH s, r ORDER BY r.timestamp DESC
WITH s, collect(r)[0] AS latest_reading
RETURN s.id AS sensor_id,
       s.name AS sensor_name,
       s.sensor_type AS sensor_type,
       latest_reading.value AS latest_value,
       latest_reading.unit AS unit,
       latest_reading.timestamp AS reading_timestamp
ORDER BY s.sensor_type, s.name
LIMIT $limit
"""

# ── Worker Analytics ──────────────────────────────────────────────────────────

WORKER_ZONE_MATRIX = """
MATCH (w)-[:LOCATED_IN|WORKS_IN|ASSIGNED_TO]->(z)
WHERE w.entity_type IN ['Worker', 'Contractor']
RETURN z.id AS zone_id,
       z.name AS zone_name,
       count(w) AS worker_count,
       collect({id: w.id, name: w.name, role: w.role}) AS workers
ORDER BY worker_count DESC
"""

WORKERS_BY_ROLE = """
MATCH (w)
WHERE w.entity_type IN ['Worker', 'Contractor']
RETURN w.role AS role, count(w) AS count
ORDER BY count DESC
"""

# ── Compliance Analytics ──────────────────────────────────────────────────────

COMPLIANCE_STATUS = """
MATCH (e)-[:COMPLIES_WITH|REFERENCED_BY]->(reg)
WHERE reg.entity_type IN ['Regulation', 'Policy', 'Standard']
RETURN e.entity_type AS entity_type,
       e.id AS entity_id,
       e.name AS entity_name,
       collect(DISTINCT reg.name) AS regulations,
       count(reg) AS compliance_count
ORDER BY entity_type, entity_name
LIMIT $limit
"""

NON_COMPLIANT_ENTITIES = """
MATCH (e)
WHERE e.entity_type IN ['Equipment', 'Zone', 'Process']
AND NOT (e)-[:COMPLIES_WITH]->(:Regulation)
AND NOT (e)-[:COMPLIES_WITH]->(:Policy)
RETURN e.id AS entity_id,
       e.name AS name,
       e.entity_type AS entity_type
LIMIT $limit
"""
