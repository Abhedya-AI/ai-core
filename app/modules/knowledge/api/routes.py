"""
api/routes.py — Enterprise Knowledge Graph API Routes.

Full production endpoint suite for the Knowledge Graph Platform:
  - Node CRUD (GET, POST, PATCH, DELETE)
  - Relationship operations (POST, DELETE)
  - Traversal & Shortest Path (POST, GET)
  - Analytics & Centrality (POST, GET)
  - Context assembly for LLM/GraphRAG (POST)
  - Search (POST, GET)
  - Synchronization (POST)
  - Ontology & Schema (GET)
  - History & Time-Travel (GET, POST)
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.knowledge.api.dependencies import (
    get_analytics_service,
    get_assemble_context_use_case,
    get_compute_analytics_use_case,
    get_create_node_use_case,
    get_create_relationship_use_case,
    get_delete_node_use_case,
    get_delete_relationship_use_case,
    get_find_node_use_case,
    get_history_repo,
    get_history_service,
    get_neighborhood_use_case,
    get_ontology_repo,
    get_search_use_case,
    get_shortest_path_use_case,
    get_sync_batch_use_case,
    get_sync_node_use_case,
    get_traverse_use_case,
    get_update_node_use_case,
)
from app.modules.knowledge.api.schemas import (
    AnalyticsRequest,
    AnalyticsResult,
    ContextRequest,
    CreateNodeRequest,
    CreateRelationshipRequest,
    GraphContext,
    HistoryRequest,
    HistoryResult,
    NodeResponse,
    RelationshipResponse,
    RestoreRequest,
    SearchRequest,
    SearchResult,
    SyncBatchRequest,
    SyncNodeRequest,
    SyncResult,
    TraversalRequest,
    TraversalResult,
    UpdateNodeRequest,
    VisualGraphResponse,
)
from app.modules.knowledge.application.use_cases import (
    AssembleContextUseCase,
    ComputeAnalyticsUseCase,
    CreateNodeUseCase,
    CreateRelationshipUseCase,
    DeleteNodeUseCase,
    DeleteRelationshipUseCase,
    FindNodeUseCase,
    NeighborhoodUseCase,
    SearchKnowledgeGraphUseCase,
    ShortestPathUseCase,
    SyncGraphBatchUseCase,
    SyncGraphNodeUseCase,
    TraverseGraphUseCase,
    UpdateNodeUseCase,
)
from app.modules.knowledge.infrastructure.repositories.history_repository import HistoryRepository
from app.modules.knowledge.infrastructure.repositories.ontology_repository import OntologyRepository
from app.modules.knowledge.services.graph_analytics_service import GraphAnalyticsService
from app.modules.knowledge.services.graph_history_service import GraphHistoryService

router = APIRouter(prefix="/graph", tags=["Knowledge Graph Engine"])


# ── 1. Node Management ─────────────────────────────────────────────────────────

@router.post(
    "/nodes",
    response_model=StandardResponse[dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new node",
    operation_id="graph_create_node",
)
async def create_node(
    body: CreateNodeRequest,
    request: Request,
    use_case: Annotated[CreateNodeUseCase, Depends(get_create_node_use_case)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_WRITE)),
) -> StandardResponse[dict[str, Any]]:
    """Create a graph node with ontology validation."""
    request_id = getattr(request.state, "request_id", "")
    node_data = await use_case.execute(body)
    return make_response(data=node_data, trace_id=request_id, request_id=request_id)


@router.get(
    "/nodes/{node_id}",
    response_model=StandardResponse[dict[str, Any]],
    summary="Get node by ID",
    operation_id="graph_get_node_by_id",
)
async def get_node_by_id(
    node_id: str,
    request: Request,
    label: str | None = Query(default=None),
    use_case: Annotated[FindNodeUseCase, Depends(get_find_node_use_case)] = None,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Fetch node properties by ID."""
    request_id = getattr(request.state, "request_id", "")
    node_data = await use_case.execute(node_id, label=label)
    if not node_data:
        from app.api.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError(f"Node '{node_id}' not found")
    return make_response(data=node_data, trace_id=request_id, request_id=request_id)


@router.patch(
    "/nodes/{node_id}",
    response_model=StandardResponse[dict[str, Any]],
    summary="Update node properties",
    operation_id="graph_update_node",
)
async def update_node(
    node_id: str,
    body: UpdateNodeRequest,
    request: Request,
    use_case: Annotated[UpdateNodeUseCase, Depends(get_update_node_use_case)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_WRITE)),
) -> StandardResponse[dict[str, Any]]:
    """Update properties of an existing node (snapshots before update)."""
    request_id = getattr(request.state, "request_id", "")
    body.node_id = node_id
    updated = await use_case.execute(body)
    return make_response(data=updated, trace_id=request_id, request_id=request_id)


@router.delete(
    "/nodes/{node_id}",
    response_model=StandardResponse[dict[str, bool]],
    summary="Delete a node",
    operation_id="graph_delete_node",
)
async def delete_node(
    node_id: str,
    request: Request,
    use_case: Annotated[DeleteNodeUseCase, Depends(get_delete_node_use_case)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_WRITE)),
) -> StandardResponse[dict[str, bool]]:
    """Detach and delete a node from the graph."""
    request_id = getattr(request.state, "request_id", "")
    success = await use_case.execute(node_id, deleted_by=principal.user_id)
    return make_response(data={"deleted": success}, trace_id=request_id, request_id=request_id)


# ── 2. Relationship Management ────────────────────────────────────────────────

@router.post(
    "/relationships",
    response_model=StandardResponse[RelationshipResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a relationship edge",
    operation_id="graph_create_relationship",
)
async def create_relationship(
    body: CreateRelationshipRequest,
    request: Request,
    use_case: Annotated[CreateRelationshipUseCase, Depends(get_create_relationship_use_case)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_WRITE)),
) -> StandardResponse[RelationshipResponse]:
    """Create a directed relationship edge between source and target nodes."""
    request_id = getattr(request.state, "request_id", "")
    success = await use_case.execute(body)
    rel_type_str = body.rel_type.value if hasattr(body.rel_type, "value") else str(body.rel_type)
    res = RelationshipResponse(
        source_id=body.source_id,
        target_id=body.target_id,
        rel_type=rel_type_str,
        properties=body.properties,
        success=success,
    )
    return make_response(data=res, trace_id=request_id, request_id=request_id)


@router.delete(
    "/relationships",
    response_model=StandardResponse[dict[str, bool]],
    summary="Delete a relationship edge",
    operation_id="graph_delete_relationship",
)
async def delete_relationship(
    source_id: str = Query(...),
    rel_type: str = Query(...),
    target_id: str = Query(...),
    request: Request = None,
    use_case: Annotated[DeleteRelationshipUseCase, Depends(get_delete_relationship_use_case)] = None,
    principal: Principal = Depends(require_permission(Permission.GRAPH_WRITE)),
) -> StandardResponse[dict[str, bool]]:
    """Delete a directed edge between two nodes."""
    request_id = getattr(request.state, "request_id", "")
    success = await use_case.execute(source_id, rel_type, target_id)
    return make_response(data={"deleted": success}, trace_id=request_id, request_id=request_id)


# ── 3. Traversal & Neighborhood ───────────────────────────────────────────────

@router.post(
    "/traverse",
    response_model=StandardResponse[TraversalResult],
    summary="Multi-hop graph traversal",
    operation_id="graph_traverse",
)
async def traverse_graph(
    body: TraversalRequest,
    request: Request,
    use_case: Annotated[TraverseGraphUseCase, Depends(get_traverse_use_case)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[TraversalResult]:
    """Execute multi-hop traversal query."""
    request_id = getattr(request.state, "request_id", "")
    res = await use_case.execute(body)
    return make_response(data=res, trace_id=request_id, request_id=request_id)


@router.get(
    "/neighborhood/{node_id}",
    response_model=StandardResponse[VisualGraphResponse],
    summary="Get k-hop neighborhood graph",
    operation_id="graph_get_neighborhood",
)
async def get_neighborhood(
    node_id: str,
    request: Request,
    hops: int = Query(default=2, ge=1, le=5),
    limit: int = Query(default=200, ge=1, le=500),
    use_case: Annotated[NeighborhoodUseCase, Depends(get_neighborhood_use_case)] = None,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[VisualGraphResponse]:
    """Extract a k-hop neighborhood network ({nodes, edges}) for visual visualizer."""
    request_id = getattr(request.state, "request_id", "")
    nb_data = await use_case.execute(node_id, hops=hops, limit=limit)
    res = VisualGraphResponse(
        center_node_id=node_id,
        nodes=nb_data.get("nodes", []),
        edges=nb_data.get("edges", []),
        total_nodes=len(nb_data.get("nodes", [])),
        total_edges=len(nb_data.get("edges", [])),
    )
    return make_response(data=res, trace_id=request_id, request_id=request_id)


@router.get(
    "/shortest-path",
    response_model=StandardResponse[dict[str, Any]],
    summary="Find shortest path between two nodes",
    operation_id="graph_shortest_path",
)
async def get_shortest_path(
    source_id: str = Query(...),
    target_id: str = Query(...),
    request: Request = None,
    use_case: Annotated[ShortestPathUseCase, Depends(get_shortest_path_use_case)] = None,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Compute shortest path between source and target nodes."""
    request_id = getattr(request.state, "request_id", "")
    path = await use_case.execute(source_id, target_id)
    if not path:
        return make_response(
            data={"found": False, "source_id": source_id, "target_id": target_id},
            trace_id=request_id,
            request_id=request_id,
        )
    path["found"] = True
    return make_response(data=path, trace_id=request_id, request_id=request_id)


# ── 4. Analytics ──────────────────────────────────────────────────────────────

@router.post(
    "/analytics",
    response_model=StandardResponse[AnalyticsResult],
    summary="Compute graph analytics algorithm",
    operation_id="graph_compute_analytics",
)
async def compute_analytics(
    body: AnalyticsRequest,
    request: Request,
    use_case: Annotated[ComputeAnalyticsUseCase, Depends(get_compute_analytics_use_case)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[AnalyticsResult]:
    """Execute graph analytics (degree, PageRank, community, impact, similarity)."""
    request_id = getattr(request.state, "request_id", "")
    result = await use_case.execute(body)
    return make_response(data=result, trace_id=request_id, request_id=request_id)


# ── 5. Context Assembly (LLM / GraphRAG) ──────────────────────────────────────

@router.post(
    "/context",
    response_model=StandardResponse[GraphContext],
    summary="Assemble graph context for LLM / GraphRAG",
    operation_id="graph_assemble_context",
)
async def assemble_context(
    body: ContextRequest,
    request: Request,
    use_case: Annotated[AssembleContextUseCase, Depends(get_assemble_context_use_case)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[GraphContext]:
    """Assemble graph context window for LLM prompt injection."""
    request_id = getattr(request.state, "request_id", "")
    context = await use_case.execute(body)
    return make_response(data=context, trace_id=request_id, request_id=request_id)


# ── 6. Search ─────────────────────────────────────────────────────────────────

@router.post(
    "/search",
    response_model=StandardResponse[SearchResult],
    summary="Search Knowledge Graph",
    operation_id="graph_search",
)
async def search_graph(
    body: SearchRequest,
    request: Request,
    use_case: Annotated[SearchKnowledgeGraphUseCase, Depends(get_search_use_case)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[SearchResult]:
    """Execute full-text, property, structural, or proximity graph search."""
    request_id = getattr(request.state, "request_id", "")
    result = await use_case.execute(body)
    return make_response(data=result, trace_id=request_id, request_id=request_id)


# ── 7. Synchronization ────────────────────────────────────────────────────────

@router.post(
    "/sync/node",
    response_model=StandardResponse[SyncResult],
    summary="Sync domain node into Knowledge Graph",
    operation_id="graph_sync_node",
)
async def sync_node(
    body: SyncNodeRequest,
    request: Request,
    use_case: Annotated[SyncGraphNodeUseCase, Depends(get_sync_node_use_case)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_WRITE)),
) -> StandardResponse[SyncResult]:
    """Upsert a single domain node into Neo4j via MERGE."""
    request_id = getattr(request.state, "request_id", "")
    result = await use_case.execute(body)
    return make_response(data=result, trace_id=request_id, request_id=request_id)


@router.post(
    "/sync/batch",
    response_model=StandardResponse[SyncResult],
    summary="Batch sync domain nodes",
    operation_id="graph_sync_batch",
)
async def sync_batch(
    body: SyncBatchRequest,
    request: Request,
    use_case: Annotated[SyncGraphBatchUseCase, Depends(get_sync_batch_use_case)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_WRITE)),
) -> StandardResponse[SyncResult]:
    """Batch upsert domain nodes into Neo4j."""
    request_id = getattr(request.state, "request_id", "")
    result = await use_case.execute(body)
    return make_response(data=result, trace_id=request_id, request_id=request_id)


# ── 8. Ontology & Schema ──────────────────────────────────────────────────────

@router.get(
    "/ontology",
    response_model=StandardResponse[dict[str, Any]],
    summary="Get Industrial Safety Ontology schema",
    operation_id="graph_get_ontology",
)
async def get_ontology(
    request: Request,
    ontology_repo: Annotated[OntologyRepository, Depends(get_ontology_repo)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Return full Industrial Safety Ontology registry summary + active DB constraints."""
    request_id = getattr(request.state, "request_id", "")
    schema = await ontology_repo.get_schema_summary()
    return make_response(data=schema, trace_id=request_id, request_id=request_id)


# ── 9. History & Versioning ───────────────────────────────────────────────────

@router.get(
    "/history/{node_id}",
    response_model=StandardResponse[HistoryResult],
    summary="Get node version history",
    operation_id="graph_get_node_history",
)
async def get_node_history(
    node_id: str,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    history_service: Annotated[GraphHistoryService, Depends(get_history_service)] = None,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[HistoryResult]:
    """Retrieve temporal snapshot history for a node with property-level diffs."""
    request_id = getattr(request.state, "request_id", "")
    req = HistoryRequest(node_id=node_id, limit=limit)
    res = await history_service.get_history(req)
    return make_response(data=res, trace_id=request_id, request_id=request_id)


@router.post(
    "/history/restore",
    response_model=StandardResponse[dict[str, Any]],
    summary="Restore node from snapshot",
    operation_id="graph_restore_snapshot",
)
async def restore_snapshot(
    body: RestoreRequest,
    request: Request,
    history_service: Annotated[GraphHistoryService, Depends(get_history_service)],
    principal: Principal = Depends(require_permission(Permission.GRAPH_WRITE)),
) -> StandardResponse[dict[str, Any]]:
    """Restore a node to the property state captured in a historical snapshot."""
    request_id = getattr(request.state, "request_id", "")
    restored = await history_service.restore_version(body.node_id, body.snapshot_id)
    return make_response(data=restored, trace_id=request_id, request_id=request_id)
