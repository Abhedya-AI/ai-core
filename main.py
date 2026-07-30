"""
main.py — ABHEDYA application entry point.

Responsibility: assemble the FastAPI application only.
No business logic. No database queries. No configuration loading.
All of that lives in the appropriate modules.

Sprint 4 Middleware Chain (applied in registration order, outermost first):
  ErrorHandlerMiddleware   — global exception → ErrorResponse conversion
  MetricsMiddleware        — per-request latency + status tracking
  RequestIDMiddleware      — UUID trace ID propagation
  RateLimitMiddleware      — sliding-window identity-tier rate limits
  RequestLoggingMiddleware — structured request/response logging
  CORSMiddleware           — cross-origin resource sharing
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.logging.middleware import RequestLoggingMiddleware
from app.api.middleware import (
    ErrorHandlerMiddleware,
    MetricsMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
)
from app.api.v1 import api_v1_router
from app.api.v1.health import router as health_router
from app.modules.vision.api.routes import router as vision_router

# ── Application ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app.name,
    version="4.0.0",
    description=(
        "ABHEDYA — Production AI Safety Platform. "
        "Multi-agent knowledge graphs, GraphRAG++, incident intelligence, "
        "emergency response, compliance, and real-time streaming."
    ),
    debug=settings.app.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Middleware ─────────────────────────────────────────────────────────────────
# Starlette applies middleware in REVERSE registration order.
# CORSMiddleware must be innermost (registered last) so preflight OPTIONS
# responses are generated before auth/rate-limit middleware see them.

app.add_middleware(CORSMiddleware,
    allow_origins=settings.security.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(ErrorHandlerMiddleware)


# ── Routes ─────────────────────────────────────────────────────────────────────

# Root health check (unauthenticated, no prefix)
app.include_router(health_router)

# Vision Intelligence Module (Sprint 2, maintained for compatibility)
app.include_router(
    vision_router,
    prefix=settings.app.api_prefix,
)

# All Sprint 4 v1 API routes (auth, incidents, workflows, admin, ws, etc.)
app.include_router(
    api_v1_router,
    prefix=settings.app.api_prefix,
)


@app.get("/", tags=["Root"], summary="Application status", operation_id="root_status")
async def root():
    """Return basic application identity, version, and status."""
    return {
        "name": settings.app.name,
        "version": "4.0.0",
        "sprint": "Sprint 4 — Production Platform",
        "status": "running",
        "environment": settings.app.environment,
        "docs": "/docs",
        "health": "/health",
        "api": settings.app.api_prefix,
    }


# ── Dev runner ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app.debug,
    )
