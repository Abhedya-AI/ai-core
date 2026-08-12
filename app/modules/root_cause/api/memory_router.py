from fastapi import APIRouter, Depends, Request, Query, HTTPException
from pydantic import BaseModel
from app.api.responses import StandardResponse, PaginatedResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.permissions import Permission
from app.core.logging import get_logger
from app.modules.root_cause.memory.memory_service import MemoryService

log = get_logger("root_cause.api.memory")
router = APIRouter()

class SearchQuery(BaseModel):
    query: str
    limit: int = 20

class SimilarQuery(BaseModel):
    investigation_id: str
    top_k: int = 5

@router.get("/memory")
async def list_memories(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    zone_id: str | None = None,
    _ = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, 'request_id', '')
    service = MemoryService()
    return make_response({"items": [], "page": page, "page_size": page_size, "zone_id": zone_id})

@router.get("/memory/{investigation_id}")
async def get_memory(
    investigation_id: str,
    request: Request,
    _ = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, 'request_id', '')
    service = MemoryService()
    return make_response({"investigation_id": investigation_id})

@router.post("/memory/search")
async def search_memory(
    payload: SearchQuery,
    request: Request,
    _ = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, 'request_id', '')
    service = MemoryService()
    return make_response({"results": [], "query": payload.query, "limit": payload.limit})

@router.post("/memory/similar")
async def similar_memory(
    payload: SimilarQuery,
    request: Request,
    _ = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, 'request_id', '')
    service = MemoryService()
    return make_response({"similar": [], "investigation_id": payload.investigation_id, "top_k": payload.top_k})
