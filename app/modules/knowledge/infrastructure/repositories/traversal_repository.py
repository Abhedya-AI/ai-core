"""
repositories/traversal_repository.py — Graph Traversal Repository.

Provides BFS, DFS, shortest path, all paths, neighborhood expansion,
impact analysis, risk propagation, and worker exposure mapping.

All methods use parameterized Cypher and fall back to empty results
(never raises) so callers always receive a valid response.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("knowledge.repository.traversal")


def _node_to_dict(node: Any) -> dict[str, Any]:
    """Safely convert a Neo4j Node object to a plain dict."""
    if node is None:
        return {}
    if isinstance(node, dict):
        return node
    if hasattr(node, "_properties"):
        return dict(node._properties)
    try:
        return dict(node)
    except Exception:
        return {}


class TraversalRepository(BaseNeo4jRepository):
    """Repository for multi-hop graph traversal operations."""

    # ── BFS / DFS ─────────────────────────────────────────────────────────────

    async def bfs_traverse(
        self,
        start_node_id: str,
        max_depth: int = 3,
        rel_types: list[str] | None = None,
        direction: str = "OUTGOING",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        BFS traversal from a start node up to max_depth hops.

        Returns list of {node: dict, depth: int, path_ids: list[str]}.
        """
        if direction == "OUTGOING":
            arrow = "-[*1..$max_depth]->"
        elif direction == "INCOMING":
            arrow = "<-[*1..$max_depth]-"
        else:
            arrow = "-[*1..$max_depth]-"

        cypher = f"""
MATCH path = (start {{id: $start_id}}){arrow}(n)
WHERE n.id <> $start_id
WITH n, length(path) AS depth, [node IN nodes(path) | node.id] AS path_ids
RETURN DISTINCT n, depth, path_ids
ORDER BY depth
LIMIT $limit
"""
        params: dict[str, Any] = {
            "start_id": start_node_id,
            "max_depth": max_depth,
            "limit": limit,
        }
        try:
            records = await self.execute_query(cypher, params)
            result = []
            for rec in records:
                result.append({
                    "node": _node_to_dict(rec.get("n")),
                    "depth": rec.get("depth", 0),
                    "path_ids": rec.get("path_ids", []),
                })
            log.info(f"BFS from {start_node_id}: found {len(result)} nodes")
            return result
        except Exception as exc:
            log.error(f"BFS traversal failed for {start_node_id}: {exc}")
            return []

    async def dfs_traverse(
        self,
        start_node_id: str,
        max_depth: int = 5,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        DFS-style traversal — returns deepest paths first.
        """
        cypher = """
MATCH path = (start {id: $start_id})-[*1..$max_depth]->(n)
WITH n, length(path) AS depth, [node IN nodes(path) | node.id] AS path_ids
RETURN DISTINCT n, depth, path_ids
ORDER BY depth DESC
LIMIT $limit
"""
        params = {"start_id": start_node_id, "max_depth": max_depth, "limit": limit}
        try:
            records = await self.execute_query(cypher, params)
            return [
                {
                    "node": _node_to_dict(rec.get("n")),
                    "depth": rec.get("depth", 0),
                    "path_ids": rec.get("path_ids", []),
                }
                for rec in records
            ]
        except Exception as exc:
            log.error(f"DFS traversal failed for {start_node_id}: {exc}")
            return []

    # ── Shortest Path ─────────────────────────────────────────────────────────

    async def shortest_path(
        self,
        start_node_id: str,
        target_node_id: str,
        max_hops: int = 10,
    ) -> dict[str, Any] | None:
        """
        Find the shortest path between two nodes.

        Returns {nodes: list[dict], length: int, node_ids: list[str]} or None.
        """
        cypher = """
MATCH (a {id: $start_id}), (b {id: $target_id})
MATCH path = shortestPath((a)-[*..10]-(b))
RETURN path,
       length(path) AS path_length,
       [node IN nodes(path) | node.id] AS node_ids,
       [node IN nodes(path) | node.entity_type] AS node_types
"""
        params = {"start_id": start_node_id, "target_id": target_node_id}
        try:
            records = await self.execute_query(cypher, params)
            if not records:
                return None
            rec = records[0]
            path_obj = rec.get("path")
            path_nodes: list[dict] = []
            if path_obj and hasattr(path_obj, "nodes"):
                path_nodes = [_node_to_dict(n) for n in path_obj.nodes]
            return {
                "nodes": path_nodes,
                "length": rec.get("path_length", 0),
                "node_ids": rec.get("node_ids", []),
                "node_types": rec.get("node_types", []),
            }
        except Exception as exc:
            log.warning(f"Shortest path {start_node_id}->{target_node_id} failed: {exc}")
            return None

    async def all_paths(
        self,
        start_node_id: str,
        target_node_id: str,
        max_depth: int = 5,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Find all paths between two nodes up to max_depth."""
        cypher = """
MATCH (a {id: $start_id}), (b {id: $target_id})
MATCH path = (a)-[*1..$max_depth]-(b)
RETURN length(path) AS path_length,
       [node IN nodes(path) | node.id] AS node_ids,
       [node IN nodes(path) | node.entity_type] AS node_types
ORDER BY path_length
LIMIT $limit
"""
        params = {
            "start_id": start_node_id,
            "target_id": target_node_id,
            "max_depth": max_depth,
            "limit": limit,
        }
        try:
            records = await self.execute_query(cypher, params)
            return [
                {
                    "length": rec.get("path_length", 0),
                    "node_ids": rec.get("node_ids", []),
                    "node_types": rec.get("node_types", []),
                }
                for rec in records
            ]
        except Exception as exc:
            log.error(f"All paths {start_node_id}->{target_node_id} failed: {exc}")
            return []

    # ── Neighborhood ──────────────────────────────────────────────────────────

    async def get_neighborhood(
        self,
        node_id: str,
        hops: int = 2,
        limit: int = 200,
    ) -> dict[str, Any]:
        """
        Return {nodes: list[dict], edges: list[dict]} for k-hop neighborhood.
        """
        cypher = """
MATCH (center {id: $node_id})-[r]-(neighbor)
RETURN DISTINCT neighbor, r, type(r) AS rel_type, properties(r) AS rel_props
LIMIT $limit
"""
        params = {"node_id": node_id, "limit": limit}
        try:
            records = await self.execute_query(cypher, params)
            nodes: list[dict] = []
            edges: list[dict] = []
            seen_node_ids: set[str] = set()
            for rec in records:
                nb = _node_to_dict(rec.get("neighbor"))
                nb_id = nb.get("id", "")
                if nb_id and nb_id not in seen_node_ids:
                    nodes.append(nb)
                    seen_node_ids.add(nb_id)
                rel_props = rec.get("rel_props") or {}
                edges.append({
                    "source_id": node_id,
                    "target_id": nb_id,
                    "rel_type": rec.get("rel_type", ""),
                    "properties": dict(rel_props),
                })
            log.info(f"Neighborhood {node_id}: {len(nodes)} nodes, {len(edges)} edges")
            return {"center_id": node_id, "nodes": nodes, "edges": edges}
        except Exception as exc:
            log.error(f"Neighborhood expansion failed for {node_id}: {exc}")
            return {"center_id": node_id, "nodes": [], "edges": []}

    # ── Impact Analysis ───────────────────────────────────────────────────────

    async def impact_analysis(
        self,
        node_id: str,
        max_depth: int = 5,
        direction: str = "OUTGOING",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Find all nodes affected downstream (OUTGOING) or upstream (INCOMING).

        Returns list of {node: dict, distance: int, path_ids: list[str]}.
        """
        if direction == "OUTGOING":
            arrow = "-[*1..$max_depth]->"
        else:
            arrow = "<-[*1..$max_depth]-"

        cypher = f"""
MATCH (source {{id: $node_id}})
MATCH path = (source){arrow}(affected)
WHERE affected.id <> $node_id
WITH affected, min(length(path)) AS distance, path
RETURN affected, distance,
       [n IN nodes(path) | n.id] AS path_ids,
       affected.entity_type AS entity_type
ORDER BY distance
LIMIT $limit
"""
        params = {"node_id": node_id, "max_depth": max_depth, "limit": limit}
        try:
            records = await self.execute_query(cypher, params)
            return [
                {
                    "node": _node_to_dict(rec.get("affected")),
                    "distance": rec.get("distance", 0),
                    "path_ids": rec.get("path_ids", []),
                    "entity_type": rec.get("entity_type", ""),
                }
                for rec in records
            ]
        except Exception as exc:
            log.error(f"Impact analysis failed for {node_id}: {exc}")
            return []

    async def dependency_graph(
        self,
        node_id: str,
        max_depth: int = 5,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Find all upstream dependencies of a node."""
        return await self.impact_analysis(
            node_id, max_depth=max_depth, direction="INCOMING", limit=limit
        )

    # ── Risk / Hazard Propagation ─────────────────────────────────────────────

    async def risk_propagation(
        self,
        hazard_node_id: str,
        max_depth: int = 4,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Trace risk propagation through HAS_RISK, AFFECTS, CAUSES, TRIGGERS relationships.
        """
        cypher = """
MATCH (hazard {id: $hazard_id})
MATCH path = (hazard)-[:HAS_RISK|AFFECTS|CAUSES|TRIGGERS*1..$max_depth]->(target)
WHERE target.id <> $hazard_id
WITH target, min(length(path)) AS hop_count, [n IN nodes(path) | n.id] AS path_ids
RETURN target, hop_count, path_ids,
       target.entity_type AS entity_type,
       target.name AS name,
       coalesce(target.risk_level, target.severity) AS risk_level
ORDER BY hop_count
LIMIT $limit
"""
        params = {"hazard_id": hazard_node_id, "max_depth": max_depth, "limit": limit}
        try:
            records = await self.execute_query(cypher, params)
            return [
                {
                    "node": _node_to_dict(rec.get("target")),
                    "distance": rec.get("hop_count", 0),
                    "path_ids": rec.get("path_ids", []),
                    "entity_type": rec.get("entity_type", ""),
                    "name": rec.get("name", ""),
                    "risk_level": rec.get("risk_level", ""),
                }
                for rec in records
            ]
        except Exception as exc:
            log.error(f"Risk propagation failed for {hazard_node_id}: {exc}")
            return []

    # ── Worker Exposure ───────────────────────────────────────────────────────

    async def worker_exposure(self, zone_id: str) -> list[dict[str, Any]]:
        """Find workers exposed to hazards in a zone."""
        cypher = """
MATCH (zone {id: $zone_id})
MATCH (worker)-[:LOCATED_IN|WORKS_IN|ASSIGNED_TO]->(zone)
WHERE worker.entity_type IN ['Worker', 'Contractor', 'Visitor']
OPTIONAL MATCH (zone)-[:HAS_RISK]->(hazard)
RETURN DISTINCT worker,
       worker.name AS worker_name,
       worker.role AS role,
       collect(DISTINCT hazard.id) AS hazard_ids,
       collect(DISTINCT hazard.title) AS hazard_names
"""
        params = {"zone_id": zone_id}
        try:
            records = await self.execute_query(cypher, params)
            return [
                {
                    "worker": _node_to_dict(rec.get("worker")),
                    "name": rec.get("worker_name", ""),
                    "role": rec.get("role", ""),
                    "hazard_ids": rec.get("hazard_ids", []),
                    "hazard_names": rec.get("hazard_names", []),
                }
                for rec in records
            ]
        except Exception as exc:
            log.error(f"Worker exposure for zone {zone_id} failed: {exc}")
            return []

    # ── Equipment Connectivity ────────────────────────────────────────────────

    async def equipment_connectivity(
        self,
        equipment_id: str,
        max_hops: int = 3,
    ) -> dict[str, Any]:
        """Find all equipment connected via CONNECTED_TO or PART_OF relationships."""
        cypher = """
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
        params = {"equipment_id": equipment_id, "max_hops": max_hops}
        try:
            records = await self.execute_query(cypher, params)
            connected = [
                {
                    "node": _node_to_dict(rec.get("related")),
                    "distance": rec.get("distance", 0),
                    "name": rec.get("name", ""),
                    "code": rec.get("code", ""),
                    "status": rec.get("status", ""),
                }
                for rec in records
            ]
            return {"equipment_id": equipment_id, "connected": connected, "total": len(connected)}
        except Exception as exc:
            log.error(f"Equipment connectivity for {equipment_id} failed: {exc}")
            return {"equipment_id": equipment_id, "connected": [], "total": 0}
