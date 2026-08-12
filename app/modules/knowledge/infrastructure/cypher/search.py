"""
cypher/search.py — Search and Discovery Cypher Query Constants.

Text search, property matching, proximity-based discovery.
All parameterized with $param syntax.
"""

# ── Full-Text Search (property CONTAINS) ──────────────────────────────────────

FULL_TEXT_ANY_NODE = """
MATCH (n)
WHERE ($label IS NULL OR n.entity_type = $label)
  AND (
    toLower(coalesce(n.name, '')) CONTAINS toLower($query)
    OR toLower(coalesce(n.title, '')) CONTAINS toLower($query)
    OR toLower(coalesce(n.code, '')) CONTAINS toLower($query)
    OR toLower(coalesce(n.description, '')) CONTAINS toLower($query)
  )
RETURN n,
       n.entity_type AS label,
       n.id AS node_id,
       n.name AS name,
       n.code AS code
ORDER BY n.entity_type, n.name
SKIP $skip
LIMIT $limit
"""

FULL_TEXT_COUNT = """
MATCH (n)
WHERE ($label IS NULL OR n.entity_type = $label)
  AND (
    toLower(coalesce(n.name, '')) CONTAINS toLower($query)
    OR toLower(coalesce(n.title, '')) CONTAINS toLower($query)
    OR toLower(coalesce(n.code, '')) CONTAINS toLower($query)
  )
RETURN count(n) AS total
"""

# ── Property Exact and Pattern Match ─────────────────────────────────────────

PROPERTY_EXACT_MATCH = """
MATCH (n)
WHERE n.entity_type = $entity_type
  AND n[$property_name] = $property_value
RETURN n
SKIP $skip
LIMIT $limit
"""

FIND_BY_CODE = """
MATCH (n {code: $code})
RETURN n, labels(n)[0] AS label, n.id AS node_id, n.name AS name
"""

FIND_BY_EXTERNAL_ID = """
MATCH (n)
WHERE n.external_id = $external_id
   OR n.source_id = $external_id
RETURN n, n.entity_type AS label, n.id AS node_id
LIMIT 10
"""

# ── Entity-Specific Searches ──────────────────────────────────────────────────

FIND_WORKERS_BY_NAME = """
MATCH (w)
WHERE w.entity_type IN ['Worker', 'Contractor', 'Visitor']
  AND toLower(w.name) CONTAINS toLower($query)
RETURN w,
       w.name AS name,
       w.role AS role,
       w.entity_type AS worker_type
ORDER BY w.name
LIMIT $limit
"""

FIND_EQUIPMENT_BY_CODE_OR_NAME = """
MATCH (e:Equipment)
WHERE toLower(e.name) CONTAINS toLower($query)
   OR toLower(e.code) CONTAINS toLower($query)
RETURN e,
       e.name AS name,
       e.code AS code,
       e.status AS status
ORDER BY e.code
LIMIT $limit
"""

FIND_SENSORS_IN_ZONE = """
MATCH (s:Sensor)-[:MONITORS|LOCATED_IN]->(z {id: $zone_id})
RETURN s,
       s.name AS name,
       s.sensor_type AS sensor_type,
       s.status AS status
ORDER BY s.sensor_type
"""

FIND_INCIDENTS_BY_STATUS = """
MATCH (i:Incident)
WHERE i.status = $status
RETURN i,
       i.title AS title,
       i.status AS status,
       i.severity AS severity,
       i.timestamp AS timestamp
ORDER BY i.timestamp DESC
SKIP $skip
LIMIT $limit
"""

FIND_HAZARDS_BY_SEVERITY = """
MATCH (h:Hazard)
WHERE h.severity = $severity OR h.risk_level = $severity
RETURN h,
       h.title AS title,
       h.severity AS severity,
       h.risk_level AS risk_level
ORDER BY h.title
LIMIT $limit
"""

FIND_ZONES_BY_RISK = """
MATCH (z:Zone)
WHERE z.risk_level = $risk_level
RETURN z,
       z.name AS name,
       z.code AS code,
       z.risk_level AS risk_level
ORDER BY z.name
LIMIT $limit
"""

FIND_ACTIVE_ALERTS = """
MATCH (a:Alert)
WHERE a.status IN ['ACTIVE', 'TRIGGERED', 'UNACKNOWLEDGED']
   OR ($severity IS NULL OR a.severity = $severity)
RETURN a,
       a.message AS message,
       a.severity AS severity,
       a.timestamp AS timestamp
ORDER BY a.timestamp DESC
LIMIT $limit
"""

# ── Multi-Label Search ─────────────────────────────────────────────────────────

MULTI_LABEL_NAME_SEARCH = """
UNWIND $entity_types AS entity_type
MATCH (n)
WHERE n.entity_type = entity_type
  AND toLower(coalesce(n.name, '')) CONTAINS toLower($query)
RETURN n,
       entity_type AS label,
       n.id AS node_id,
       n.name AS name
ORDER BY label, name
LIMIT $limit
"""

# ── Proximity / Graph Distance Search ─────────────────────────────────────────

PROXIMITY_SEARCH = """
MATCH (center {id: $center_node_id})
MATCH (center)-[*1..$max_hops]-(nearby)
WHERE nearby.id <> $center_node_id
  AND ($filter_type IS NULL OR nearby.entity_type = $filter_type)
WITH DISTINCT nearby
RETURN nearby,
       nearby.entity_type AS label,
       nearby.id AS node_id,
       nearby.name AS name
LIMIT $limit
"""

NODES_SHARING_RELATIONSHIP_TARGET = """
MATCH (a {id: $node_id})-[:$rel_type]->(shared)<-[:$rel_type]-(similar)
WHERE similar.id <> $node_id
WITH similar, count(shared) AS common_count
RETURN similar,
       similar.entity_type AS label,
       similar.name AS name,
       common_count
ORDER BY common_count DESC
LIMIT $limit
"""

# ── Keyword Index Search (Neo4j full-text if available) ───────────────────────

FULLTEXT_INDEX_SEARCH = """
CALL db.index.fulltext.queryNodes($index_name, $query)
YIELD node, score
RETURN node,
       node.id AS node_id,
       node.entity_type AS label,
       node.name AS name,
       score
ORDER BY score DESC
LIMIT $limit
"""
