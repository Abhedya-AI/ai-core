"""
app/api/v1/analytics.py — Telemetry, Analytics, and Trajectory Explorer API.

Endpoints:
  GET /analytics/summary      — Aggregate metrics & plant health snapshot
  GET /analytics/agents       — Agent execution telemetry breakdown
  GET /analytics/trajectories/{task_id} — Detailed SupervisorAgent execution trajectory
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.responses import StandardResponse, make_response
from app.core.observability.metrics import SystemMetricsRegistry
from app.core.observability.tracing import TracerStore
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission

router = APIRouter(prefix="/analytics", tags=["Analytics & Telemetry"])


def _get_metrics() -> SystemMetricsRegistry:
    return SystemMetricsRegistry.get_instance()


def _get_tracer() -> TracerStore:
    return TracerStore.get_instance()


@router.get(
    "/summary",
    response_model=StandardResponse[dict],
    summary="Get plant safety analytics summary",
    operation_id="analytics_summary",
)
async def get_analytics_summary(
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ANALYTICS_READ)),
    metrics: SystemMetricsRegistry = Depends(_get_metrics),
) -> StandardResponse[dict]:
    """Return an aggregated snapshot of system risk evaluations and agent metrics."""
    request_id = getattr(request.state, "request_id", "")
    data = {
        "metrics": metrics.summary(),
        "status": "HEALTHY",
    }
    return make_response(data=data, trace_id=request_id, request_id=request_id)


@router.get(
    "/agents",
    response_model=StandardResponse[dict],
    summary="Get agent telemetry breakdown",
    operation_id="analytics_agent_telemetry",
)
async def get_agent_telemetry(
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ANALYTICS_READ)),
    metrics: SystemMetricsRegistry = Depends(_get_metrics),
) -> StandardResponse[dict]:
    """Return per-agent execution counts, success/failure rates, and average latencies."""
    request_id = getattr(request.state, "request_id", "")
    return make_response(data=metrics.summary()["agents"], trace_id=request_id, request_id=request_id)


@router.get(
    "/trajectories/{task_id}",
    response_model=StandardResponse[dict],
    summary="Get SupervisorAgent execution trajectory trace",
    operation_id="analytics_trajectory_trace",
)
async def get_trajectory_trace(
    task_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ANALYTICS_READ)),
    tracer: TracerStore = Depends(_get_tracer),
) -> StandardResponse[dict]:
    """Return the step-by-step reasoning and execution trajectory spans for a workflow task_id."""
    request_id = getattr(request.state, "request_id", "")
    trajectory = tracer.get_trajectory_summary(task_id)
    return make_response(data=trajectory, trace_id=request_id, request_id=request_id)
