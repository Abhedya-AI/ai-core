from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, Request

from app.api.responses import StandardResponse, PaginatedResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.permissions import Permission
from app.core.logging import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/evidence", tags=["Root Cause Analysis — Evidence"])

@router.get("/{investigation_id}", response_model=StandardResponse)
async def get_evidence(
    request: Request,
    investigation_id: str,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"investigation_id": investigation_id, "evidence_items": []}
    return make_response(data=data, trace_id=request_id, request_id=request_id)

@router.post("/{investigation_id}/collect", response_model=StandardResponse)
async def collect_evidence(
    request: Request,
    investigation_id: str,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"investigation_id": investigation_id, "status": "collecting"}
    return make_response(data=data, trace_id=request_id, request_id=request_id)
