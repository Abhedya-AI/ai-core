"""
app/api/v1/workflows.py — Supervisor Workflow Endpoints.

General-purpose AI workflow interface. For users who want to ask any
free-form safety question and get a multi-agent analysis.

Endpoints:
  POST /workflows        — Run a Supervisor workflow
  GET  /workflows        — List recent workflow runs
  GET  /workflows/{id}   — Get workflow status and results
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.api.responses import PaginatedResponse, PaginationMeta, ResponseMetadata, StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.services.workflow_service import WorkflowService, get_workflow_service

router = APIRouter(prefix="/workflows", tags=["AI Workflows"])


class RunWorkflowRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=2048, description="Safety question or command")
    intent: str = Field(default="GENERAL_SAFETY", description="Override intent classification")
    zone_id: str | None = None
    target_entity_id: str | None = None


@router.post(
    "",
    response_model=StandardResponse[dict],
    status_code=201,
    summary="Run a Supervisor AI workflow",
    operation_id="run_workflow",
)
async def run_workflow(
    body: RunWorkflowRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.WORKFLOW_EXECUTE)),
    svc: WorkflowService = Depends(get_workflow_service),
) -> StandardResponse[dict]:
    """
    Execute a multi-agent Supervisor workflow for any safety question.

    The Supervisor will automatically:
    - Classify the intent
    - Select the right agents
    - Run them in the optimal order
    - Return aggregated results
    """
    request_id = getattr(request.state, "request_id", "")
    result = await svc.run_workflow(
        query=body.query,
        intent=body.intent,
        zone_id=body.zone_id,
        target_entity_id=body.target_entity_id,
        principal=principal,
    )
    return make_response(data=result, trace_id=request_id, request_id=request_id)


@router.get(
    "",
    response_model=PaginatedResponse[dict],
    summary="List recent workflow runs",
    operation_id="list_workflows",
)
async def list_workflows(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    principal: Principal = Depends(require_permission(Permission.WORKFLOW_READ)),
    svc: WorkflowService = Depends(get_workflow_service),
) -> PaginatedResponse[dict]:
    """Return recent workflow executions."""
    request_id = getattr(request.state, "request_id", "")
    items = await svc.list_workflows(limit=limit)
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
    "/{task_id}",
    response_model=StandardResponse[dict],
    summary="Get workflow status and results",
    operation_id="get_workflow",
)
async def get_workflow(
    task_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.WORKFLOW_READ)),
    svc: WorkflowService = Depends(get_workflow_service),
) -> StandardResponse[dict]:
    """Get the status and results of a specific workflow run."""
    request_id = getattr(request.state, "request_id", "")
    result = await svc.get_workflow(task_id)
    return make_response(data=result, trace_id=request_id, request_id=request_id)
