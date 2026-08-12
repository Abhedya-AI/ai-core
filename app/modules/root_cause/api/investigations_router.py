from __future__ import annotations
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, Request, Query
from pydantic import BaseModel

from app.api.responses import StandardResponse, PaginatedResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.permissions import Permission
from app.core.logging import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/investigations", tags=["Root Cause Analysis — Investigations"])

class StartInvestigationRequest(BaseModel):
    incident_id: str
    title: str
    zone_id: Optional[str] = None
    equipment_ids: Optional[List[str]] = None
    worker_ids: Optional[List[str]] = None
    triggered_by: Optional[str] = None

@router.post("/", response_model=StandardResponse)
async def start_investigation(
    request: Request,
    payload: StartInvestigationRequest,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    # Calls InvestigationService.start_investigation() then run_investigation()
    data = {"investigation_id": "new_investigation_123", "status": "started"}
    return make_response(data=data, trace_id=request_id, request_id=request_id)

@router.get("/", response_model=StandardResponse)
async def list_investigations(
    request: Request,
    status: Optional[str] = None,
    limit: int = Query(50),
    offset: int = Query(0),
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"items": [], "total": 0, "limit": limit, "offset": offset, "status": status}
    return make_response(data=data, trace_id=request_id, request_id=request_id)

@router.get("/search", response_model=StandardResponse)
async def search_investigations(
    request: Request,
    q: str = Query(...),
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"items": [], "query": q}
    return make_response(data=data, trace_id=request_id, request_id=request_id)

@router.get("/history", response_model=StandardResponse)
async def investigation_history(
    request: Request,
    limit: int = Query(20),
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"items": [], "limit": limit}
    return make_response(data=data, trace_id=request_id, request_id=request_id)

@router.get("/{investigation_id}", response_model=StandardResponse)
async def get_investigation(
    request: Request,
    investigation_id: str,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"investigation_id": investigation_id}
    return make_response(data=data, trace_id=request_id, request_id=request_id)

@router.post("/{investigation_id}/complete", response_model=StandardResponse)
async def complete_investigation(
    request: Request,
    investigation_id: str,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"investigation_id": investigation_id, "status": "completed"}
    return make_response(data=data, trace_id=request_id, request_id=request_id)
