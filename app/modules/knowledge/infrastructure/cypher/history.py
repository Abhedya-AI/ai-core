"""
cypher/history.py — Temporal Versioning and Node History Cypher.

Supports the 'graph time-machine' feature:
  "What was the state of Zone X 5 minutes before the incident?"

Approach:
  - Before any mutation, create a NodeSnapshot node
  - Link it: (original_node)-[:HAS_SNAPSHOT]->(snapshot)
  - Snapshots store the full property set + version number + timestamp
"""

# ── Snapshot Creation ──────────────────────────────────────────────────────────

CREATE_NODE_SNAPSHOT = """
MATCH (n {id: $node_id})
WITH n
CREATE (snap:NodeSnapshot {
    id: $snapshot_id,
    node_id: $node_id,
    node_label: $node_label,
    version_number: $version_number,
    properties_json: $properties_json,
    change_summary: $change_summary,
    created_by: $created_by,
    created_at: $created_at,
    entity_type: 'NodeSnapshot'
})
WITH n, snap
MERGE (n)-[r:HAS_SNAPSHOT]->(snap)
ON CREATE SET r.created_at = $created_at
RETURN snap
"""

GET_NEXT_VERSION_NUMBER = """
MATCH (n {id: $node_id})-[:HAS_SNAPSHOT]->(snap:NodeSnapshot)
RETURN coalesce(max(snap.version_number), 0) + 1 AS next_version
"""

# ── Snapshot Retrieval ────────────────────────────────────────────────────────

LIST_SNAPSHOTS_FOR_NODE = """
MATCH (n {id: $node_id})-[:HAS_SNAPSHOT]->(snap:NodeSnapshot)
WHERE ($since IS NULL OR snap.created_at >= $since)
  AND ($until IS NULL OR snap.created_at <= $until)
RETURN snap
ORDER BY snap.version_number DESC
SKIP $skip
LIMIT $limit
"""

COUNT_SNAPSHOTS_FOR_NODE = """
MATCH (n {id: $node_id})-[:HAS_SNAPSHOT]->(snap:NodeSnapshot)
RETURN count(snap) AS total_versions
"""

GET_SNAPSHOT_BY_ID = """
MATCH (snap:NodeSnapshot {id: $snapshot_id})
RETURN snap
"""

GET_SNAPSHOT_AT_TIMESTAMP = """
MATCH (n {id: $node_id})-[:HAS_SNAPSHOT]->(snap:NodeSnapshot)
WHERE snap.created_at <= $timestamp
RETURN snap
ORDER BY snap.created_at DESC
LIMIT 1
"""

GET_LATEST_SNAPSHOT = """
MATCH (n {id: $node_id})-[:HAS_SNAPSHOT]->(snap:NodeSnapshot)
RETURN snap
ORDER BY snap.version_number DESC
LIMIT 1
"""

GET_OLDEST_SNAPSHOT = """
MATCH (n {id: $node_id})-[:HAS_SNAPSHOT]->(snap:NodeSnapshot)
RETURN snap
ORDER BY snap.version_number ASC
LIMIT 1
"""

# ── Snapshot Restoration ──────────────────────────────────────────────────────

RESTORE_NODE_FROM_SNAPSHOT = """
MATCH (n {id: $node_id})
MATCH (snap:NodeSnapshot {id: $snapshot_id})
SET n.properties_backup = snap.properties_json,
    n.restored_at = $now,
    n.restored_from_version = snap.version_number,
    n.updated_at = $now
RETURN n, snap
"""

# ── Snapshot Maintenance ───────────────────────────────────────────────────────

PURGE_OLD_SNAPSHOTS = """
MATCH (snap:NodeSnapshot)
WHERE snap.created_at < $cutoff_timestamp
DETACH DELETE snap
RETURN count(snap) AS deleted_count
"""

PURGE_SNAPSHOTS_FOR_NODE = """
MATCH (n {id: $node_id})-[:HAS_SNAPSHOT]->(snap:NodeSnapshot)
WHERE snap.version_number < $keep_from_version
DETACH DELETE snap
RETURN count(snap) AS deleted_count
"""

# ── Change History Queries ────────────────────────────────────────────────────

NODE_CHANGE_HISTORY = """
MATCH (n {id: $node_id})-[:HAS_SNAPSHOT]->(snap:NodeSnapshot)
RETURN snap.version_number AS version,
       snap.created_at AS changed_at,
       snap.created_by AS changed_by,
       snap.change_summary AS summary,
       snap.properties_json AS properties_json
ORDER BY snap.version_number DESC
LIMIT $limit
"""

NODES_CHANGED_IN_TIMERANGE = """
MATCH (n)-[:HAS_SNAPSHOT]->(snap:NodeSnapshot)
WHERE snap.created_at >= $start_time
  AND snap.created_at <= $end_time
  AND ($label IS NULL OR snap.node_label = $label)
RETURN DISTINCT n.id AS node_id,
       n.entity_type AS label,
       n.name AS name,
       count(snap) AS version_count,
       max(snap.created_at) AS last_changed_at
ORDER BY last_changed_at DESC
LIMIT $limit
"""

# ── Snapshot Stats ────────────────────────────────────────────────────────────

SNAPSHOT_STORAGE_STATS = """
MATCH (snap:NodeSnapshot)
RETURN count(snap) AS total_snapshots,
       count(DISTINCT snap.node_id) AS tracked_nodes,
       min(snap.created_at) AS oldest_snapshot,
       max(snap.created_at) AS newest_snapshot
"""
