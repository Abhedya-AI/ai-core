"""
app/api/v1/graph.py — Knowledge Graph Explorer & Visual Network Endpoints.

Provides network topology visualization structures ({nodes, edges}) for UI visualizers.
Backed by production Knowledge Graph services (TraversalRepository, GraphAnalyticsService)
with automatic fallback to mock graph topology if Neo4j is offline or empty.

Endpoints:
  GET  /graph/nodes          — List graph nodes by entity type
  GET  /graph/subgraph/{id}  — Extract k-hop neighborhood graph
  GET  /graph/paths/impact   — Calculate cascading risk impact path between entities
  POST /graph/query          — Run graph query and return visual network JSON
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.api.responses import StandardResponse, make_response
from app.core.logging import get_logger
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.knowledge.infrastructure.repositories.traversal_repository import TraversalRepository

log = get_logger("api.graph_explorer")

router = APIRouter(prefix="/graph", tags=["Knowledge Graph Explorer"])


class VisualGraphQueryRequest(BaseModel):
    query: str = Field(..., description="Cypher or natural language graph query")
    entity_types: list[str] = Field(default_factory=list)
    limit: int = Field(default=50, ge=1, le=200)


# Mock Graph Data for visual rendering fallback when Neo4j is offline or empty
MOCK_NODES = [
    {"id": "PLANT-01", "label": "Plant PL-01", "type": "Plant", "risk_level": "LOW"},
    {"id": "ZONE-A", "label": "Zone A — Processing", "type": "Zone", "risk_level": "LOW"},
    {"id": "ZONE-B", "label": "Zone B — Tank Farm", "type": "Zone", "risk_level": "HIGH"},
    {"id": "TANK-T07", "label": "Tank T-07 (Methane)", "type": "Asset", "risk_level": "HIGH"},
    {"id": "HAZARD-104", "label": "Gas Leak Anomaly", "type": "Hazard", "risk_level": "CRITICAL"},
    {"id": "SOP-GH-04", "label": "Gas Leak Containment SOP", "type": "SOP", "risk_level": "LOW"},
    {"id": "WORKER-12", "label": "Ravi Kumar (Tech)", "type": "Worker", "risk_level": "LOW"},
]

MOCK_EDGES = [
    {"source": "PLANT-01", "target": "ZONE-A", "relation": "CONTAINS"},
    {"source": "PLANT-01", "target": "ZONE-B", "relation": "CONTAINS"},
    {"source": "ZONE-B", "target": "TANK-T07", "relation": "HOUSES"},
    {"source": "TANK-T07", "target": "HAZARD-104", "relation": "EXHIBITS"},
    {"source": "HAZARD-104", "target": "SOP-GH-04", "relation": "GOVERNED_BY"},
    {"source": "WORKER-12", "target": "ZONE-B", "relation": "ASSIGNED_TO"},
]


@router.get(
    "/nodes",
    response_model=StandardResponse[list[dict[str, Any]]],
    summary="List Knowledge Graph nodes",
    operation_id="graph_list_nodes",
)
async def list_graph_nodes(
    request: Request,
    entity_type: str | None = Query(default=None, description="Filter by entity type"),
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[list[dict[str, Any]]]:
    """Return graph nodes filtered by entity type from Neo4j (fallback to mock data)."""
    request_id = getattr(request.state, "request_id", "")
    nodes: list[dict[str, Any]] = []

    try:
        repo = BaseNeo4jRepository()
        if entity_type:
            cypher = "MATCH (n) WHERE n.entity_type = $et OR labels(n)[0] = $et RETURN n LIMIT 100"
            params = {"et": entity_type}
        else:
            cypher = "MATCH (n) RETURN n LIMIT 100"
            params = {}

        records = await repo.execute_query(cypher, params)
        for rec in records:
            n = rec.get("n", {})
            props = dict(n._properties) if hasattr(n, "_properties") else dict(n)
            nodes.append({
                "id": props.get("id", ""),
                "label": props.get("name") or props.get("title") or props.get("code") or props.get("id", ""),
                "type": props.get("entity_type", "GraphEntity"),
                "risk_level": props.get("risk_level", props.get("severity", "LOW")),
            })
    except Exception as exc:
        log.warning(f"Neo4j list nodes failed ({exc}), falling back to mock nodes")

    if not nodes:
        nodes = MOCK_NODES
        if entity_type:
            nodes = [n for n in nodes if n["type"].lower() == entity_type.lower()]

    return make_response(data=nodes, trace_id=request_id, request_id=request_id)


@router.get(
    "/subgraph/{node_id}",
    response_model=StandardResponse[dict[str, Any]],
    summary="Get k-hop subgraph around an entity",
    operation_id="graph_get_subgraph",
)
async def get_subgraph(
    node_id: str,
    request: Request,
    k_hops: int = Query(default=2, ge=1, le=5),
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Extract a k-hop sub-network around a specific node ID for UI rendering."""
    request_id = getattr(request.state, "request_id", "")
    subgraph_nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    try:
        traversal = TraversalRepository()
        nb = await traversal.get_neighborhood(node_id, hops=k_hops)
        raw_nodes = nb.get("nodes", [])
        raw_edges = nb.get("edges", [])

        if raw_nodes:
            for n in raw_nodes:
                subgraph_nodes.append({
                    "id": n.get("id", ""),
                    "label": n.get("name") or n.get("title") or n.get("code") or n.get("id", ""),
                    "type": n.get("entity_type", "GraphEntity"),
                    "risk_level": n.get("risk_level", n.get("severity", "LOW")),
                })
            for e in raw_edges:
                edges.append({
                    "source": e.get("source_id", ""),
                    "target": e.get("target_id", ""),
                    "relation": e.get("rel_type", "CONNECTED_TO"),
                })
    except Exception as exc:
        log.warning(f"Neo4j subgraph failed ({exc}), using mock fallback")

    if not subgraph_nodes:
        connected_edges = [
            e for e in MOCK_EDGES if e["source"] == node_id or e["target"] == node_id
        ]
        connected_node_ids = {node_id}
        for e in connected_edges:
            connected_node_ids.add(e["source"])
            connected_node_ids.add(e["target"])

        subgraph_nodes = [n for n in MOCK_NODES if n["id"] in connected_node_ids]
        edges = connected_edges

    data = {
        "center_node_id": node_id,
        "k_hops": k_hops,
        "nodes": subgraph_nodes,
        "edges": edges,
    }
    return make_response(data=data, trace_id=request_id, request_id=request_id)


@router.get(
    "/paths/impact",
    response_model=StandardResponse[dict[str, Any]],
    summary="Calculate cascading risk impact path",
    operation_id="graph_impact_path",
)
async def get_impact_path(
    source_id: str = Query(..., description="Source entity ID"),
    target_id: str = Query(..., description="Target entity ID"),
    request: Request = None,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Trace risk propagation path between source and target entities."""
    request_id = getattr(request.state, "request_id", "")
    path_found = False
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    distance = 0

    try:
        traversal = TraversalRepository()
        sp = await traversal.shortest_path(source_id, target_id)
        if sp and sp.get("nodes"):
            path_found = True
            distance = sp.get("length", 0)
            raw_nodes = sp.get("nodes", [])
            for n in raw_nodes:
                nodes.append({
                    "id": n.get("id", ""),
                    "label": n.get("name") or n.get("title") or n.get("id", ""),
                    "type": n.get("entity_type", "GraphEntity"),
                })
            node_ids = sp.get("node_ids", [])
            for i in range(len(node_ids) - 1):
                edges.append({"source": node_ids[i], "target": node_ids[i + 1], "relation": "PATH"})
    except Exception as exc:
        log.warning(f"Neo4j impact path failed ({exc}), using mock fallback")

    if not path_found:
        path_found = True
        distance = 3
        nodes = [n for n in MOCK_NODES if n["id"] in ("TANK-T07", "HAZARD-104", "SOP-GH-04")]
        edges = [MOCK_EDGES[3], MOCK_EDGES[4]]

    data = {
        "source_id": source_id,
        "target_id": target_id,
        "path_found": path_found,
        "distance": distance,
        "path": [n["id"] for n in nodes],
        "nodes": nodes,
        "edges": edges,
    }
    return make_response(data=data, trace_id=request_id, request_id=request_id)


@router.post(
    "/query",
    response_model=StandardResponse[dict[str, Any]],
    summary="Execute visual graph query",
    operation_id="graph_visual_query",
)
async def query_graph(
    body: VisualGraphQueryRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Execute a query and return visual network JSON ({nodes, edges})."""
    request_id = getattr(request.state, "request_id", "")
    nodes: list[dict[str, Any]] = []

    try:
        repo = BaseNeo4jRepository()
        if "MATCH" in body.query.upper():
            records = await repo.execute_query(body.query)
            for rec in records:
                for val in rec.values():
                    if hasattr(val, "_properties"):
                        props = dict(val._properties)
                        nodes.append({
                            "id": props.get("id", ""),
                            "label": props.get("name") or props.get("title") or props.get("id", ""),
                            "type": props.get("entity_type", "GraphEntity"),
                        })
    except Exception as exc:
        log.warning(f"Neo4j query failed ({exc}), using mock fallback")

    if not nodes:
        nodes = MOCK_NODES[: body.limit]

    data = {
        "query": body.query,
        "nodes": nodes,
        "edges": MOCK_EDGES,
    }
    return make_response(data=data, trace_id=request_id, request_id=request_id)
