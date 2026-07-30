"""
app/api/v1/incidents.py — Incident Management Endpoints.

These are business endpoints — they never mention agents.
The frontend/caller works with "incidents", "investigations", "findings".
The fact that agents are running is an implementation detail.

Endpoints:
  POST /incidents                    — Create incident (+ auto-investigate)
  GET  /incidents                    — List recent incidents
  GET  /incidents/{incident_id}      — Get incident detail
  POST /incidents/{incident_id}/investigate  — Re-trigger investigation
  POST /incidents/{incident_id}/close        — Close incident
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.api.responses import PaginatedResponse, PaginationMeta, ResponseMetadata, StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.services.incident_service import IncidentService, get_incident_service

router = APIRouter(prefix="/incidents", tags=["Incident Management"])


# ── Request Schemas ────────────────────────────────────────────────────────────

class CreateIncidentRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=256, description="Short incident title")
    description: str = Field(..., min_length=10, description="Detailed description or AI query")
    zone_id: str | None = Field(default=None, description="Affected zone ID")
    target_entity_id: str | None = Field(default=None, description="Primary asset/entity ID")
    severity: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    auto_investigate: bool = Field(default=True, description="Immediately trigger AI investigation")


class CloseIncidentRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=10, max_length=2048)


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=StandardResponse[dict],
    status_code=201,
    summary="Create a new incident",
    operation_id="create_incident",
)
async def create_incident(
    body: CreateIncidentRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.INCIDENT_CREATE)),
    svc: IncidentService = Depends(get_incident_service),
) -> StandardResponse[dict]:
    """Create a new incident record. If auto_investigate=true, triggers AI investigation immediately."""
    request_id = getattr(request.state, "request_id", "")
    incident = await svc.create_incident(
        title=body.title,
        description=body.description,
        zone_id=body.zone_id,
        target_entity_id=body.target_entity_id,
        severity=body.severity,
        principal=principal,
        auto_investigate=body.auto_investigate,
    )
    return make_response(data=incident, trace_id=request_id, request_id=request_id)


@router.get(
    "",
    response_model=PaginatedResponse[dict],
    summary="List recent incidents",
    operation_id="list_incidents",
)
async def list_incidents(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    principal: Principal = Depends(require_permission(Permission.INCIDENT_READ)),
    svc: IncidentService = Depends(get_incident_service),
) -> PaginatedResponse[dict]:
    """Return a paginated list of recent incidents."""
    request_id = getattr(request.state, "request_id", "")
    items = await svc.list_incidents(limit=limit)
    return PaginatedResponse(
        data=items,
        pagination=PaginationMeta(
            total=len(items),
            page=1,
            page_size=limit,
            has_next=False,
            has_prev=False,
        ),
        metadata=ResponseMetadata(trace_id=request_id, request_id=request_id),
    )


@router.get(
    "/{incident_id}",
    response_model=StandardResponse[dict],
    summary="Get incident by ID",
    operation_id="get_incident",
)
async def get_incident(
    incident_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.INCIDENT_READ)),
    svc: IncidentService = Depends(get_incident_service),
) -> StandardResponse[dict]:
    """Retrieve full incident details including investigation results."""
    request_id = getattr(request.state, "request_id", "")
    incident = await svc.get_incident(incident_id)
    return make_response(data=incident, trace_id=request_id, request_id=request_id)


@router.post(
    "/{incident_id}/investigate",
    response_model=StandardResponse[dict],
    summary="Re-trigger AI investigation",
    operation_id="investigate_incident",
)
async def investigate_incident(
    incident_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.INCIDENT_INVESTIGATE)),
    svc: IncidentService = Depends(get_incident_service),
) -> StandardResponse[dict]:
    """Run the full Supervisor multi-agent investigation on an existing incident."""
    request_id = getattr(request.state, "request_id", "")
    incident = await svc.investigate(incident_id, principal=principal)
    return make_response(data=incident, trace_id=request_id, request_id=request_id)


@router.post(
    "/{incident_id}/close",
    response_model=StandardResponse[dict],
    summary="Close an incident",
    operation_id="close_incident",
)
async def close_incident(
    incident_id: str,
    body: CloseIncidentRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.INCIDENT_CLOSE)),
    svc: IncidentService = Depends(get_incident_service),
) -> StandardResponse[dict]:
    """Mark an incident as closed with resolution notes."""
    request_id = getattr(request.state, "request_id", "")
    incident = await svc.close_incident(incident_id, body.resolution_notes, principal=principal)
    return make_response(data=incident, trace_id=request_id, request_id=request_id)
