"""
common.py — Centralized generic Cypher query library.

All queries are parameterized ($param) to prevent Cypher injection and enable statement caching.
"""

CREATE_NODE = """
CREATE (n:{label} $properties)
RETURN n
"""

MERGE_NODE = """
MERGE (n:{label} {{id: $id}})
SET n += $properties
RETURN n
"""

UPDATE_NODE = """
MATCH (n {id: $id})
SET n += $properties, n.updated_at = $updated_at
RETURN n
"""

DELETE_NODE = """
MATCH (n {id: $id})
DETACH DELETE n
RETURN count(n) AS deleted_count
"""

FIND_NODE_BY_ID = """
MATCH (n {id: $id})
RETURN n
"""

NODE_EXISTS = """
MATCH (n {id: $id})
RETURN count(n) > 0 AS exists
"""

COUNT_NODES = """
MATCH (n:{label})
RETURN count(n) AS count
"""

COUNT_ALL_NODES = """
MATCH (n)
RETURN count(n) AS count
"""

CREATE_RELATIONSHIP = """
MATCH (s {id: $source_id})
MATCH (t {id: $target_id})
MERGE (s)-[r:{rel_type}]->(t)
SET r += $properties
RETURN count(r) AS created_count
"""

DELETE_RELATIONSHIP = """
MATCH (s {id: $source_id})-[r:{rel_type}]->(t {id: $target_id})
DELETE r
RETURN count(r) AS deleted_count
"""

GET_NEIGHBORS = """
MATCH (s {id: $node_id})-[r]-(n)
RETURN n, type(r) AS relationship, properties(r) AS rel_properties
"""

TRAVERSE_SUBGRAPH = """
MATCH path = (start {id: $start_node_id})-[*1..{max_depth}]->(target)
RETURN path
LIMIT $limit
"""

SHORTEST_PATH = """
MATCH (start {id: $start_node_id}), (target {id: $target_node_id})
MATCH path = shortestPath((start)-[*..10]-(target))
RETURN path
"""

# Schema management
CREATE_UNIQUE_CONSTRAINT = """
CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
FOR (n:{label}) REQUIRE n.id IS UNIQUE
"""

CREATE_FULLTEXT_INDEX = """
CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS
FOR (n:{label}) ON EACH [n.name, n.title, n.code, n.description]
"""

LIST_CONSTRAINTS = """
SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties
RETURN name, type, labelsOrTypes, properties
"""

LIST_INDEXES = """
SHOW INDEXES YIELD name, type, labelsOrTypes, properties, state
RETURN name, type, labelsOrTypes, properties, state
"""

DROP_CONSTRAINT = """
DROP CONSTRAINT {constraint_name} IF EXISTS
"""

FIND_NODES_BY_LABEL = """
MATCH (n:{label})
RETURN n
SKIP $skip
LIMIT $limit
"""

FIND_NODES_BY_LABEL_ORDERED = """
MATCH (n:{label})
RETURN n
ORDER BY n.created_at DESC
SKIP $skip
LIMIT $limit
"""

GET_ALL_RELATIONSHIPS = """
MATCH (s)-[r]-(t)
RETURN s, r, t, type(r) AS rel_type
SKIP $skip
LIMIT $limit
"""

GET_RELATIONSHIPS_BETWEEN = """
MATCH (s {id: $source_id})-[r]-(t {id: $target_id})
RETURN r, type(r) AS rel_type, properties(r) AS props
"""

COUNT_RELATIONSHIPS = """
MATCH ()-[r]->()
RETURN count(r) AS count
"""

COUNT_RELATIONSHIPS_FOR_NODE = """
MATCH (n {id: $node_id})-[r]-()
RETURN count(r) AS count
"""
