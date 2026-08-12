"""
repositories/analytics_repository.py — Graph Analytics Repository.

Provides degree centrality, PageRank approximation, community detection,
risk distribution, and subgraph statistics backed by Neo4j.

Falls back to in-memory GraphIntelligenceEngine for algorithms
that require GDS or complex computation.
"""
from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("knowledge.repository.analytics")


def _node_to_dict(node: Any) -> dict[str, Any]:
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


class AnalyticsRepository(BaseNeo4jRepository):
    """Repository for graph analytics computations."""

    # ── Degree Centrality ─────────────────────────────────────────────────────

    async def degree_centrality(
        self,
        label: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Compute total degree (in + out) for all nodes of a given label.

        Returns ranked list of {node_id, label, name, degree, rank}.
        """
        if label:
            cypher = """
MATCH (n)-[r]-()
WHERE n.entity_type = $label
WITH n, count(r) AS degree
RETURN n.id AS node_id, n.entity_type AS label, n.name AS name, degree
ORDER BY degree DESC
LIMIT $limit
"""
            params: dict[str, Any] = {"label": label, "limit": limit}
        else:
            cypher = """
MATCH (n)-[r]-()
WITH n, count(r) AS degree
RETURN n.id AS node_id, n.entity_type AS label, n.name AS name, degree
ORDER BY degree DESC
LIMIT $limit
"""
            params = {"limit": limit}

        try:
            records = await self.execute_query(cypher, params)
            return [
                {
                    "node_id": rec.get("node_id", ""),
                    "label": rec.get("label", ""),
                    "name": rec.get("name"),
                    "score": float(rec.get("degree", 0)),
                    "rank": idx + 1,
                }
                for idx, rec in enumerate(records)
            ]
        except Exception as exc:
            log.error(f"Degree centrality failed: {exc}")
            return []

    async def in_degree_centrality(
        self,
        label: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Nodes with most incoming relationships."""
        if label:
            cypher = """
MATCH (n)<-[r]-()
WHERE n.entity_type = $label
WITH n, count(r) AS in_degree
RETURN n.id AS node_id, n.entity_type AS label, n.name AS name, in_degree
ORDER BY in_degree DESC
LIMIT $limit
"""
            params: dict[str, Any] = {"label": label, "limit": limit}
        else:
            cypher = """
MATCH (n)<-[r]-()
WITH n, count(r) AS in_degree
RETURN n.id AS node_id, n.entity_type AS label, n.name AS name, in_degree
ORDER BY in_degree DESC
LIMIT $limit
"""
            params = {"limit": limit}

        try:
            records = await self.execute_query(cypher, params)
            return [
                {
                    "node_id": rec.get("node_id", ""),
                    "label": rec.get("label", ""),
                    "name": rec.get("name"),
                    "score": float(rec.get("in_degree", 0)),
                    "rank": idx + 1,
                }
                for idx, rec in enumerate(records)
            ]
        except Exception as exc:
            log.error(f"In-degree centrality failed: {exc}")
            return []

    async def out_degree_centrality(
        self,
        label: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Nodes with most outgoing relationships."""
        if label:
            cypher = """
MATCH (n)-[r]->()
WHERE n.entity_type = $label
WITH n, count(r) AS out_degree
RETURN n.id AS node_id, n.entity_type AS label, n.name AS name, out_degree
ORDER BY out_degree DESC
LIMIT $limit
"""
            params: dict[str, Any] = {"label": label, "limit": limit}
        else:
            cypher = """
MATCH (n)-[r]->()
WITH n, count(r) AS out_degree
RETURN n.id AS node_id, n.entity_type AS label, n.name AS name, out_degree
ORDER BY out_degree DESC
LIMIT $limit
"""
            params = {"limit": limit}

        try:
            records = await self.execute_query(cypher, params)
            return [
                {
                    "node_id": rec.get("node_id", ""),
                    "label": rec.get("label", ""),
                    "name": rec.get("name"),
                    "score": float(rec.get("out_degree", 0)),
                    "rank": idx + 1,
                }
                for idx, rec in enumerate(records)
            ]
        except Exception as exc:
            log.error(f"Out-degree centrality failed: {exc}")
            return []

    async def pagerank_in_memory(
        self,
        label: str | None = None,
        iterations: int = 20,
        damping: float = 0.85,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Approximate PageRank using GraphIntelligenceEngine (no GDS required).

        Delegates to the in-memory engine which runs iterative PageRank.
        """
        t0 = time.monotonic()
        try:
            from app.modules.knowledge.graph_intelligence.graph_intelligence_engine import (
                GraphIntelligenceEngine,
            )
            engine = GraphIntelligenceEngine(repository=self)
            scores: dict[str, float] = engine.pagerank(
                damping_factor=damping,
                max_iterations=iterations,
            )
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
            results = []
            for rank, (node_id, score) in enumerate(ranked, 1):
                node_data = engine._nodes.get(node_id, {})
                results.append({
                    "node_id": node_id,
                    "label": node_data.get("type", node_data.get("entity_type", "")),
                    "name": node_data.get("name"),
                    "score": round(score, 6),
                    "rank": rank,
                })
            elapsed = (time.monotonic() - t0) * 1000
            log.info(f"PageRank computed in {elapsed:.1f}ms, {len(results)} nodes")
            return results
        except Exception as exc:
            log.error(f"PageRank computation failed: {exc}")
            return []

    # ── Community Detection ───────────────────────────────────────────────────

    async def community_detection(
        self,
        label: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        """
        Detect communities using GraphIntelligenceEngine label propagation.

        Returns {total_communities, total_nodes, communities: {id: [node_ids]}}.
        """
        try:
            from app.modules.knowledge.graph_intelligence.graph_intelligence_engine import (
                GraphIntelligenceEngine,
            )
            engine = GraphIntelligenceEngine(repository=self)
            communities = engine.label_propagation_communities()
            # communities: dict[str, int]  node_id -> community_id
            grouped: dict[int, list[str]] = {}
            for node_id, comm_id in communities.items():
                grouped.setdefault(comm_id, []).append(node_id)

            # Convert to member dicts
            community_members: dict[int, list[dict[str, Any]]] = {}
            for comm_id, members in grouped.items():
                member_list = []
                for nid in members[:50]:  # cap per community
                    node_data = engine._nodes.get(nid, {})
                    member_list.append({
                        "node_id": nid,
                        "label": node_data.get("type", ""),
                        "name": node_data.get("name"),
                        "community_id": comm_id,
                    })
                community_members[comm_id] = member_list

            return {
                "total_communities": len(grouped),
                "total_nodes": len(communities),
                "largest_community_size": max((len(v) for v in grouped.values()), default=0),
                "communities": community_members,
            }
        except Exception as exc:
            log.error(f"Community detection failed: {exc}")
            return {"total_communities": 0, "total_nodes": 0, "communities": {}}

    # ── Connected Components ──────────────────────────────────────────────────

    async def connected_components(
        self,
        label: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find weakly connected components using Neo4j queries.
        Returns list of {component_id, size, node_ids}.
        """
        cypher = """
MATCH (n)
WHERE ($label IS NULL OR n.entity_type = $label)
OPTIONAL MATCH (n)-[]-(neighbor)
RETURN n.id AS node_id, n.entity_type AS label, collect(DISTINCT neighbor.id) AS neighbor_ids
LIMIT $limit
"""
        params: dict[str, Any] = {"label": label, "limit": 500}
        try:
            records = await self.execute_query(cypher, params)
            # Build adjacency and run BFS
            adj: dict[str, set[str]] = {}
            for rec in records:
                nid = rec.get("node_id", "")
                neighbors = [n for n in (rec.get("neighbor_ids") or []) if n]
                adj[nid] = set(neighbors)

            visited: set[str] = set()
            components: list[list[str]] = []
            for node in adj:
                if node not in visited:
                    component: list[str] = []
                    queue = [node]
                    while queue:
                        curr = queue.pop()
                        if curr in visited:
                            continue
                        visited.add(curr)
                        component.append(curr)
                        queue.extend(adj.get(curr, set()) - visited)
                    components.append(component)

            return [
                {"component_id": idx, "size": len(comp), "node_ids": comp}
                for idx, comp in enumerate(sorted(components, key=len, reverse=True))
            ]
        except Exception as exc:
            log.error(f"Connected components failed: {exc}")
            return []

    # ── Risk Distribution ─────────────────────────────────────────────────────

    async def risk_distribution(self) -> dict[str, Any]:
        """Count nodes by risk_level / severity across all entity types."""
        cypher = """
MATCH (n)
WHERE n.risk_level IS NOT NULL OR n.severity IS NOT NULL
RETURN n.entity_type AS entity_type,
       coalesce(n.risk_level, n.severity) AS level,
       count(n) AS count
ORDER BY entity_type, level
"""
        try:
            records = await self.execute_query(cypher, {})
            distribution: dict[str, dict[str, int]] = {}
            for rec in records:
                et = rec.get("entity_type", "Unknown")
                level = rec.get("level", "UNKNOWN")
                cnt = rec.get("count", 0)
                distribution.setdefault(et, {})[level] = cnt
            return distribution
        except Exception as exc:
            log.error(f"Risk distribution failed: {exc}")
            return {}

    # ── Subgraph Statistics ───────────────────────────────────────────────────

    async def subgraph_stats(
        self,
        entity_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return total nodes, relationships, counts by label and relationship type."""
        cypher_nodes = """
MATCH (n)
RETURN labels(n)[0] AS label, count(n) AS count
ORDER BY count DESC
"""
        cypher_rels = """
MATCH ()-[r]->()
RETURN type(r) AS rel_type, count(r) AS count
ORDER BY count DESC
"""
        try:
            node_records = await self.execute_query(cypher_nodes, {})
            rel_records = await self.execute_query(cypher_rels, {})

            by_label = {rec["label"]: rec["count"] for rec in node_records if rec.get("label")}
            by_rel = {rec["rel_type"]: rec["count"] for rec in rel_records if rec.get("rel_type")}

            # Filter by entity_types if provided
            if entity_types:
                by_label = {k: v for k, v in by_label.items() if k in entity_types}

            return {
                "total_nodes": sum(by_label.values()),
                "total_relationships": sum(by_rel.values()),
                "by_label": by_label,
                "by_rel_type": by_rel,
            }
        except Exception as exc:
            log.error(f"Subgraph stats failed: {exc}")
            return {"total_nodes": 0, "total_relationships": 0, "by_label": {}, "by_rel_type": {}}

    # ── Node Similarity ───────────────────────────────────────────────────────

    async def node_similarity(
        self,
        node_id_a: str,
        node_id_b: str,
    ) -> dict[str, Any]:
        """Jaccard similarity based on common neighbors."""
        cypher = """
MATCH (a {id: $node_id_a})-[]-(common)-[]-(b {id: $node_id_b})
WHERE a.id <> b.id
WITH count(DISTINCT common) AS common_count, collect(DISTINCT common.id) AS common_ids
MATCH (a {id: $node_id_a})-[]-()
WITH common_count, common_ids, count(DISTINCT a) AS size_a
MATCH (b {id: $node_id_b})-[]-()
WITH common_count, common_ids, size_a, count(DISTINCT b) AS size_b
RETURN common_count, common_ids, size_a, size_b,
       CASE (size_a + size_b - common_count)
           WHEN 0 THEN 0.0
           ELSE toFloat(common_count) / (size_a + size_b - common_count)
       END AS jaccard_score
"""
        params = {"node_id_a": node_id_a, "node_id_b": node_id_b}
        try:
            records = await self.execute_query(cypher, params)
            if not records:
                return {
                    "node_id_a": node_id_a,
                    "node_id_b": node_id_b,
                    "jaccard_score": 0.0,
                    "common_neighbors": 0,
                    "common_neighbor_ids": [],
                }
            rec = records[0]
            return {
                "node_id_a": node_id_a,
                "node_id_b": node_id_b,
                "jaccard_score": round(float(rec.get("jaccard_score", 0.0)), 4),
                "common_neighbors": rec.get("common_count", 0),
                "common_neighbor_ids": rec.get("common_ids", []),
            }
        except Exception as exc:
            log.error(f"Node similarity {node_id_a}/{node_id_b} failed: {exc}")
            return {"node_id_a": node_id_a, "node_id_b": node_id_b, "jaccard_score": 0.0, "common_neighbors": 0}
