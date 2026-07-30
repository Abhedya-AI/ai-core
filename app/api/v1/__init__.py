"""
app/api/v1/__init__.py — API v1 router aggregation.

All v1 routers are collected here and exposed as `api_v1_router`.
main.py mounts this once under /api/v1.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.admin import router as admin_router
from app.api.v1.websocket import router as ws_router
from app.api.v1.health import router as health_router

# Existing routers from previous milestones
from app.api.v1.emergency import router as emergency_router
from app.api.v1.graph import router as graph_router
from app.api.v1.rag import router as rag_router
from app.api.v1.root_cause import router as root_cause_router
from app.api.v1.agent import router as agent_router


api_v1_router = APIRouter()

# Auth — public & protected identity endpoints
api_v1_router.include_router(auth_router)

# Business domain endpoints (all auth-protected)
api_v1_router.include_router(incidents_router)
api_v1_router.include_router(workflows_router)
api_v1_router.include_router(admin_router)

# Legacy / module-specific routers from Sprint 3
api_v1_router.include_router(emergency_router)
api_v1_router.include_router(graph_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(root_cause_router)
api_v1_router.include_router(agent_router)

# Health checks (separate, no auth required)
api_v1_router.include_router(health_router)

# WebSocket streaming (auth via query param)
api_v1_router.include_router(ws_router)

__all__ = ["api_v1_router"]
