from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.responses import StandardResponse, PaginatedResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.permissions import Permission
from app.core.logging import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/hypotheses", tags=["Root Cause Analysis — Hypotheses"])

class RejectHypothesisRequest(BaseModel):
    reason: str

@router.get("/{investigation_id}", response_model=StandardResponse)
async def list_hypotheses(
    request: Request,
    investigation_id: str,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"investigation_id": investigation_id, "hypotheses": []}
    return make_response(data=data, trace_id=request_id, request_id=request_id)

@router.post("/{investigation_id}/{hypothesis_id}/confirm", response_model=StandardResponse)
async def confirm_hypothesis(
    request: Request,
    investigation_id: str,
    hypothesis_id: str,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {"investigation_id": investigation_id, "hypothesis_id": hypothesis_id, "status": "confirmed"}
    return make_response(data=data, trace_id=request_id, request_id=request_id)

@router.post("/{investigation_id}/{hypothesis_id}/reject", response_model=StandardResponse)
async def reject_hypothesis(
    request: Request,
    investigation_id: str,
    hypothesis_id: str,
    payload: RejectHypothesisRequest,
    principal: Any = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, "request_id", "")
    data = {
        "investigation_id": investigation_id, 
        "hypothesis_id": hypothesis_id, 
        "status": "rejected", 
        "reason": payload.reason
    }
    return make_response(data=data, trace_id=request_id, request_id=request_id)
