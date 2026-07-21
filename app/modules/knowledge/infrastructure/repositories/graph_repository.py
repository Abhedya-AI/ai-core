"""
graph_repository.py — Generic Graph Repository for graph-wide algorithms and search queries.
"""

from typing import Any

from app.modules.knowledge.application.dto import (
    GraphSearchRequest,
    TraversalRequest,
    TraversalResult,
)
from app.modules.knowledge.application.interfaces.graph_search import IGraphSearchEngine
from app.modules.knowledge.infrastructure.cypher import common as common_cypher
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository


class Neo4jGraphRepository(BaseNeo4jRepository, IGraphSearchEngine):
    """
    Graph-wide repository providing algorithms, pattern searches,
    shortest path queries, and subgraph extractions.
    """

    async def find_shortest_path(self, start_id: str, target_id: str, max_depth: int = 5) -> list[dict[str, Any]]:
        """Find shortest path between two nodes in the graph."""
        records = await self.execute_query(
            common_cypher.SHORTEST_PATH,
            {"start_node_id": start_id, "target_node_id": target_id},
        )
        if records:
            p = records[0].get("path")
            if p and hasattr(p, "nodes"):
                return [dict(n._properties) if hasattr(n, "_properties") else dict(n) for n in p.nodes]
        return []

    async def get_subgraph(self, center_node_id: str, depth: int = 2) -> TraversalResult:
        """Extract a sub-graph centered around center_node_id."""
        req = TraversalRequest(start_node_id=center_node_id, max_depth=depth)
        return await self.traverse(req)

    async def search(self, request: GraphSearchRequest) -> list[dict[str, Any]]:
        """Structured pattern search across graph nodes and relationships."""
        label = request.start_criteria.label or "GraphEntity"
        query = f"MATCH (n:{label}) "
        params: dict[str, Any] = {}

        if request.start_criteria.properties:
            conditions = []
            for idx, (k, v) in enumerate(request.start_criteria.properties.items()):
                p_name = f"p_{idx}"
                conditions.append(f"n.{k} = ${p_name}")
                params[p_name] = v
            query += f"WHERE {' AND '.join(conditions)} "

        query += f"RETURN n LIMIT {request.limit}"
        records = await self.execute_query(query, params)
        return [r.get("n", {}) for r in records]

    async def node_degree(self, node_id: str) -> int:
        """Calculate the in+out degree of a given node."""
        query = "MATCH (n {id: $id})-[r]-() RETURN count(r) AS degree"
        records = await self.execute_query(query, {"id": node_id})
        if records:
            return int(records[0].get("degree", 0))
        return 0
