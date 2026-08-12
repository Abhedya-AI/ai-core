from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, Request

from app.api.responses import StandardResponse, PaginatedResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.permissions import Permission
from app.core.logging import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/reports", tags=["Root Cause Analysis — Reports"])

@router.get("/{investigation_id}", response_model=StandardResponse)
async def get_full_report(
    request: Request,
    investigation_id: str,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"investigation_id": investigation_id, "report_data": {}}
    return make_response(data=data, trace_id=request_id, request_id=request_id)

@router.get("/{investigation_id}/summary", response_model=StandardResponse)
async def get_executive_summary(
    request: Request,
    investigation_id: str,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"investigation_id": investigation_id, "executive_summary": {}}
    return make_response(data=data, trace_id=request_id, request_id=request_id)

@router.get("/{investigation_id}/markdown", response_model=StandardResponse)
async def get_markdown_report(
    request: Request,
    investigation_id: str,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    markdown_content = f"# Investigation Report: {investigation_id}\n\nContent goes here."
    data = {"investigation_id": investigation_id, "markdown": markdown_content}
    return make_response(data=data, trace_id=request_id, request_id=request_id)
