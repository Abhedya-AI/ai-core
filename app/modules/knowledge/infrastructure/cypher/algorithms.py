"""
cypher/algorithms.py — Graph Algorithm Cypher Query Constants.

All queries are parameterized ($param) to prevent Cypher injection
and enable statement caching. Never use f-strings inside Cypher strings
for user-supplied values.

Conventions:
  - Group by algorithm family
  - Use UPPERCASE_SNAKE for constant names
  - Relationship direction: OUTGOING by default
  - All paths queries use LIMIT to protect against explosion
"""

# ── BFS / DFS Traversal ────────────────────────────────────────────────────────

BFS_FROM_NODE = """
MATCH path = (start {id: $start_id})-[*1..$max_depth]->(n)
WHERE start.id = $start_id
WITH n, length(path) AS depth, path
RETURN DISTINCT n, depth, path
ORDER BY depth
LIMIT $limit
"""

DFS_TRAVERSE = """
MATCH path = (start {id: $start_id})-[*1..$max_depth]->(n)
RETURN n, length(path) AS depth, [node IN nodes(path) | node.id] AS path_ids
ORDER BY length(path) DESC
LIMIT $limit
"""

BFS_UNDIRECTED = """
MATCH path = (start {id: $start_id})-[*1..$max_depth]-(n)
WHERE n.id <> $start_id
WITH n, min(length(path)) AS depth
RETURN n, depth
ORDER BY depth
LIMIT $limit
"""

# ── Shortest Path ──────────────────────────────────────────────────────────────

SHORTEST_PATH_UNWEIGHTED = """
MATCH (a {id: $start_id}), (b {id: $target_id})
MATCH path = shortestPath((a)-[*..10]-(b))
RETURN path,
       length(path) AS path_length,
       [node IN nodes(path) | node.id] AS node_ids,
       [node IN nodes(path) | node.entity_type] AS node_types
"""

SHORTEST_PATH_DIRECTED = """
MATCH (a {id: $start_id}), (b {id: $target_id})
MATCH path = shortestPath((a)-[*..10]->(b))
RETURN path,
       length(path) AS path_length,
       [node IN nodes(path) | node.id] AS node_ids,
       [node IN nodes(path) | node.entity_type] AS node_types
"""

ALL_PATHS_BETWEEN = """
MATCH (a {id: $start_id}), (b {id: $target_id})
MATCH path = (a)-[*1..$max_depth]-(b)
RETURN path,
       length(path) AS path_length,
       [node IN nodes(path) | node.id] AS node_ids
ORDER BY path_length
LIMIT $limit
"""

# ── Neighborhood Expansion ────────────────────────────────────────────────────

NEIGHBORHOOD_K_HOP = """
MATCH (center {id: $node_id})-[r*1..$hops]-(neighbor)
WHERE neighbor.id <> $node_id
WITH DISTINCT neighbor, r
RETURN collect(DISTINCT neighbor) AS nodes,
       collect(DISTINCT r) AS relationships
LIMIT $limit
"""

NEIGHBORHOOD_NODES_ONLY = """
MATCH (center {id: $node_id})-[*1..$hops]-(neighbor)
WHERE neighbor.id <> $node_id
RETURN DISTINCT neighbor, labels(neighbor)[0] AS label
ORDER BY neighbor.entity_type, neighbor.name
LIMIT $limit
"""

NEIGHBORHOOD_WITH_EDGES = """
MATCH (center {id: $node_id})-[r]-(neighbor)
RETURN neighbor, r, type(r) AS rel_type, properties(r) AS rel_props
LIMIT $limit
"""

# ── Impact Analysis ────────────────────────────────────────────────────────────

IMPACT_ANALYSIS_DOWNSTREAM = """
MATCH (source {id: $node_id})
MATCH path = (source)-[*1..$max_depth]->(affected)
WHERE affected.id <> $node_id
WITH affected, min(length(path)) AS distance, path
RETURN affected,
       distance,
       [n IN nodes(path) | n.id] AS path_ids,
       affected.entity_type AS entity_type,
       affected.name AS name
ORDER BY distance
LIMIT $limit
"""

IMPACT_ANALYSIS_UPSTREAM = """
MATCH (source {id: $node_id})
MATCH path = (dependency)-[*1..$max_depth]->(source)
WHERE dependency.id <> $node_id
WITH dependency, min(length(path)) AS distance, path
RETURN dependency,
       distance,
       [n IN nodes(path) | n.id] AS path_ids,
       dependency.entity_type AS entity_type,
       dependency.name AS name
ORDER BY distance
LIMIT $limit
"""

# ── Risk Propagation ──────────────────────────────────────────────────────────

RISK_PROPAGATION = """
MATCH (hazard {id: $hazard_id})
MATCH path = (hazard)-[:HAS_RISK|AFFECTS|CAUSES|TRIGGERS*1..$max_depth]->(target)
WHERE target.id <> $hazard_id
WITH target,
     min(length(path)) AS hop_count,
     [n IN nodes(path) | n.id] AS path_ids
RETURN target,
       hop_count,
       path_ids,
       target.entity_type AS entity_type,
       target.name AS name,
       target.risk_level AS risk_level
ORDER BY hop_count, target.risk_level DESC
LIMIT $limit
"""

HAZARD_PROPAGATION = """
MATCH (hazard {id: $hazard_id})
MATCH path = (hazard)-[:AFFECTS|TRIGGERS|NEAR*1..$max_depth]-(affected)
WHERE affected.id <> $hazard_id
WITH DISTINCT affected, min(length(path)) AS distance
RETURN affected,
       distance,
       affected.entity_type AS entity_type,
       affected.name AS name
ORDER BY distance
LIMIT $limit
"""

CASCADING_RISK_CHAIN = """
MATCH (start {id: $start_id})
MATCH chain = (start)-[:CAUSES|LEADS_TO|TRIGGERS*1..6]->(end_node)
WITH chain, end_node,
     [n IN nodes(chain) | {id: n.id, type: n.entity_type, name: n.name}] AS chain_nodes
RETURN chain_nodes, length(chain) AS chain_length
ORDER BY chain_length DESC
LIMIT $limit
"""

# ── Worker Exposure ───────────────────────────────────────────────────────────

WORKER_EXPOSURE_IN_ZONE = """
MATCH (zone {id: $zone_id})
MATCH (worker)-[:LOCATED_IN|WORKS_IN|ASSIGNED_TO]->(zone)
WHERE worker.entity_type IN ['Worker', 'Contractor', 'Visitor']
OPTIONAL MATCH (zone)-[:HAS_RISK]->(hazard)
RETURN DISTINCT worker,
       worker.name AS worker_name,
       worker.role AS role,
       collect(DISTINCT hazard) AS hazards,
       collect(DISTINCT hazard.title) AS hazard_names
"""

WORKERS_NEAR_HAZARD = """
MATCH (hazard {id: $hazard_id})
MATCH (hazard)<-[:AFFECTS|HAS_RISK]-(zone)
MATCH (worker)-[:LOCATED_IN|WORKS_IN|ASSIGNED_TO]->(zone)
WHERE worker.entity_type IN ['Worker', 'Contractor']
RETURN DISTINCT worker,
       worker.name AS name,
       worker.role AS role,
       zone.name AS zone_name
"""

ALL_WORKER_ZONE_ASSIGNMENTS = """
MATCH (worker)-[:LOCATED_IN|WORKS_IN|ASSIGNED_TO]->(location)
WHERE worker.entity_type IN ['Worker', 'Contractor', 'Visitor']
RETURN worker,
       worker.name AS worker_name,
       worker.role AS role,
       location,
       location.name AS location_name,
       location.entity_type AS location_type
ORDER BY worker.name
"""

# ── Equipment & Sensor Connectivity ──────────────────────────────────────────

EQUIPMENT_CONNECTIVITY = """
MATCH path = (equip {id: $equipment_id})-[:CONNECTED_TO|PART_OF*1..$max_hops]-(related)
WHERE related.entity_type = 'Equipment'
WITH DISTINCT related, min(length(path)) AS distance
RETURN related,
       distance,
       related.name AS name,
       related.code AS code,
       related.status AS status
ORDER BY distance
"""

SENSOR_COVERAGE = """
MATCH (sensor)-[:MONITORS|LOCATED_IN]->(target)
WHERE sensor.entity_type = 'Sensor'
RETURN sensor,
       sensor.name AS sensor_name,
       sensor.sensor_type AS sensor_type,
       sensor.status AS sensor_status,
       target,
       target.name AS target_name,
       target.entity_type AS target_type
ORDER BY sensor.sensor_type
"""

SENSORS_FOR_EQUIPMENT = """
MATCH (sensor)-[:MONITORS]->(equip {id: $equipment_id})
WHERE sensor.entity_type = 'Sensor'
RETURN sensor,
       sensor.name AS name,
       sensor.sensor_type AS sensor_type,
       sensor.status AS status
"""

# ── Centrality Approximations ─────────────────────────────────────────────────

DEGREE_CENTRALITY_ALL = """
MATCH (n)-[r]-()
WHERE ($label IS NULL OR n.entity_type = $label)
WITH n, count(r) AS degree
RETURN n.id AS node_id,
       n.entity_type AS label,
       n.name AS name,
       degree
ORDER BY degree DESC
LIMIT $limit
"""

IN_DEGREE_CENTRALITY = """
MATCH (n)<-[r]-()
WHERE ($label IS NULL OR n.entity_type = $label)
WITH n, count(r) AS in_degree
RETURN n.id AS node_id,
       n.entity_type AS label,
       n.name AS name,
       in_degree
ORDER BY in_degree DESC
LIMIT $limit
"""

OUT_DEGREE_CENTRALITY = """
MATCH (n)-[r]->()
WHERE ($label IS NULL OR n.entity_type = $label)
WITH n, count(r) AS out_degree
RETURN n.id AS node_id,
       n.entity_type AS label,
       n.name AS name,
       out_degree
ORDER BY out_degree DESC
LIMIT $limit
"""

PAGERANK_NEIGHBOR_SCORES = """
MATCH (n)-[r]->(neighbor)
WHERE ($label IS NULL OR n.entity_type = $label)
WITH n, count(DISTINCT neighbor) AS out_links
MATCH (n)<-[r2]-(in_neighbor)
WITH n, out_links, count(DISTINCT in_neighbor) AS in_links
RETURN n.id AS node_id,
       n.entity_type AS label,
       n.name AS name,
       in_links,
       out_links,
       toFloat(in_links) / (1 + out_links) AS approx_pagerank
ORDER BY approx_pagerank DESC
LIMIT $limit
"""

# ── Node Similarity ───────────────────────────────────────────────────────────

COMMON_NEIGHBORS = """
MATCH (a {id: $node_id_a})-[]-(common)-[]-(b {id: $node_id_b})
WHERE a.id <> b.id
RETURN count(DISTINCT common) AS common_count,
       collect(DISTINCT common.id) AS common_neighbor_ids
"""

JACCARD_SIMILARITY = """
MATCH (a {id: $node_id_a})-[]-(neighbors_a)
WITH collect(DISTINCT neighbors_a.id) AS set_a
MATCH (b {id: $node_id_b})-[]-(neighbors_b)
WITH set_a, collect(DISTINCT neighbors_b.id) AS set_b
WITH set_a, set_b,
     [x IN set_a WHERE x IN set_b] AS intersection
RETURN size(intersection) AS common,
       size(set_a) AS size_a,
       size(set_b) AS size_b,
       CASE size(set_a) + size(set_b) - size(intersection)
           WHEN 0 THEN 0.0
           ELSE toFloat(size(intersection)) / (size(set_a) + size(set_b) - size(intersection))
       END AS jaccard_score
"""

# ── Connected Components (pure Cypher) ────────────────────────────────────────

WEAKLY_CONNECTED_SUBGRAPHS = """
MATCH (n)
WHERE ($label IS NULL OR n.entity_type = $label)
OPTIONAL MATCH (n)-[r]-(neighbor)
RETURN n,
       n.entity_type AS label,
       collect(DISTINCT neighbor.id) AS neighbor_ids
LIMIT $limit
"""

CYCLE_DETECTION = """
MATCH path = (start {id: $start_id})-[*2..6]->(start)
RETURN length(path) AS cycle_length,
       [n IN nodes(path) | n.id] AS cycle_node_ids
LIMIT 10
"""
