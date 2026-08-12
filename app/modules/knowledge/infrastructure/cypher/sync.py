"""
cypher/sync.py — MERGE-based Upsert Cypher for Graph Synchronization.

All sync queries use MERGE to guarantee idempotency:
  - Safe to call multiple times with the same data
  - Never creates duplicate nodes
  - Updates existing nodes with latest properties

Used by GraphSyncService when consuming Kafka events from
Sensor, Vision, Incident, and Workflow modules.
"""

# ── Generic Upsert ────────────────────────────────────────────────────────────

UPSERT_NODE_GENERIC = """
MERGE (n:{label} {{id: $id}})
ON CREATE SET n += $properties, n.entity_type = $label, n.created_at = $now
ON MATCH SET n += $properties, n.updated_at = $now
RETURN n
"""

UPSERT_RELATIONSHIP_GENERIC = """
MATCH (s {id: $source_id})
MATCH (t {id: $target_id})
MERGE (s)-[r:{rel_type}]->(t)
ON CREATE SET r += $properties, r.created_at = $now
ON MATCH SET r += $properties, r.updated_at = $now
RETURN count(r) AS upserted_count
"""

# ── Sensor Module Sync ────────────────────────────────────────────────────────

UPSERT_SENSOR_NODE = """
MERGE (s:Sensor {id: $sensor_id})
ON CREATE SET
    s.entity_type = 'Sensor',
    s.name = $name,
    s.sensor_type = $sensor_type,
    s.status = $status,
    s.location_code = $location_code,
    s.unit = $unit,
    s.source_module = 'sensor',
    s.created_at = $now,
    s.updated_at = $now
ON MATCH SET
    s.name = $name,
    s.sensor_type = $sensor_type,
    s.status = $status,
    s.location_code = $location_code,
    s.unit = $unit,
    s.updated_at = $now
RETURN s
"""

UPSERT_READING_NODE = """
MERGE (r:Reading {id: $reading_id})
ON CREATE SET
    r.entity_type = 'Reading',
    r.sensor_id = $sensor_id,
    r.value = $value,
    r.unit = $unit,
    r.timestamp = $timestamp,
    r.quality = $quality,
    r.anomaly_score = $anomaly_score,
    r.source_module = 'sensor',
    r.created_at = $now
ON MATCH SET
    r.value = $value,
    r.quality = $quality,
    r.anomaly_score = $anomaly_score,
    r.updated_at = $now
RETURN r
"""

LINK_READING_TO_SENSOR = """
MATCH (s:Sensor {id: $sensor_id})
MATCH (r:Reading {id: $reading_id})
MERGE (s)-[rel:GENERATED]->(r)
ON CREATE SET rel.created_at = $now
RETURN count(rel) AS linked
"""

# ── Equipment Module Sync ─────────────────────────────────────────────────────

UPSERT_EQUIPMENT_NODE = """
MERGE (e:Equipment {id: $equipment_id})
ON CREATE SET
    e.entity_type = 'Equipment',
    e.name = $name,
    e.code = $code,
    e.equipment_type = $equipment_type,
    e.status = $status,
    e.location_code = $location_code,
    e.manufacturer = $manufacturer,
    e.model = $model,
    e.source_module = $source_module,
    e.created_at = $now,
    e.updated_at = $now
ON MATCH SET
    e.name = $name,
    e.status = $status,
    e.equipment_type = $equipment_type,
    e.location_code = $location_code,
    e.updated_at = $now
RETURN e
"""

# ── Worker Module Sync ────────────────────────────────────────────────────────

UPSERT_WORKER_NODE = """
MERGE (w:Worker {id: $worker_id})
ON CREATE SET
    w.entity_type = 'Worker',
    w.name = $name,
    w.role = $role,
    w.email = $email,
    w.department = $department,
    w.status = $status,
    w.source_module = $source_module,
    w.created_at = $now,
    w.updated_at = $now
ON MATCH SET
    w.name = $name,
    w.role = $role,
    w.department = $department,
    w.status = $status,
    w.updated_at = $now
RETURN w
"""

# ── Zone / Location Sync ──────────────────────────────────────────────────────

UPSERT_ZONE_NODE = """
MERGE (z:Zone {id: $zone_id})
ON CREATE SET
    z.entity_type = 'Zone',
    z.name = $name,
    z.code = $code,
    z.zone_type = $zone_type,
    z.risk_level = $risk_level,
    z.capacity = $capacity,
    z.source_module = $source_module,
    z.created_at = $now,
    z.updated_at = $now
ON MATCH SET
    z.name = $name,
    z.risk_level = $risk_level,
    z.zone_type = $zone_type,
    z.updated_at = $now
RETURN z
"""

# ── Incident Module Sync ──────────────────────────────────────────────────────

UPSERT_INCIDENT_NODE = """
MERGE (i:Incident {id: $incident_id})
ON CREATE SET
    i.entity_type = 'Incident',
    i.title = $title,
    i.description = $description,
    i.status = $status,
    i.severity = $severity,
    i.timestamp = $timestamp,
    i.location_id = $location_id,
    i.source_module = 'incident',
    i.created_at = $now,
    i.updated_at = $now
ON MATCH SET
    i.title = $title,
    i.status = $status,
    i.severity = $severity,
    i.description = $description,
    i.updated_at = $now
RETURN i
"""

# ── Vision Module Sync ────────────────────────────────────────────────────────

UPSERT_DETECTION_NODE = """
MERGE (d:Detection {id: $detection_id})
ON CREATE SET
    d.entity_type = 'Detection',
    d.camera_id = $camera_id,
    d.hazard_type = $hazard_type,
    d.confidence = $confidence,
    d.risk_level = $risk_level,
    d.zone_id = $zone_id,
    d.timestamp = $timestamp,
    d.source_module = 'vision',
    d.created_at = $now
ON MATCH SET
    d.confidence = $confidence,
    d.risk_level = $risk_level,
    d.updated_at = $now
RETURN d
"""

LINK_DETECTION_TO_ZONE = """
MATCH (d:Detection {id: $detection_id})
MATCH (z {id: $zone_id})
MERGE (d)-[r:LOCATED_IN]->(z)
ON CREATE SET r.created_at = $now
RETURN count(r) AS linked
"""

LINK_DETECTION_TO_CAMERA = """
MATCH (d:Detection {id: $detection_id})
MATCH (c:Camera {id: $camera_id})
MERGE (c)-[r:GENERATED]->(d)
ON CREATE SET r.created_at = $now
RETURN count(r) AS linked
"""

# ── Alert Sync ────────────────────────────────────────────────────────────────

UPSERT_ALERT_NODE = """
MERGE (a:Alert {id: $alert_id})
ON CREATE SET
    a.entity_type = 'Alert',
    a.message = $message,
    a.severity = $severity,
    a.status = $status,
    a.source_id = $source_id,
    a.source_type = $source_type,
    a.timestamp = $timestamp,
    a.source_module = $source_module,
    a.created_at = $now
ON MATCH SET
    a.message = $message,
    a.severity = $severity,
    a.status = $status,
    a.updated_at = $now
RETURN a
"""

# ── Archival ──────────────────────────────────────────────────────────────────

ARCHIVE_NODE = """
MATCH (n {id: $node_id})
SET n.archived = true,
    n.archived_at = $now,
    n.archived_by = $archived_by
RETURN n
"""

UNARCHIVE_NODE = """
MATCH (n {id: $node_id})
REMOVE n.archived
SET n.archived_at = null,
    n.updated_at = $now
RETURN n
"""
