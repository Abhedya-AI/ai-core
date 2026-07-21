"""
main.py — ABHEDYA application entry point.

Responsibility: assemble the FastAPI application only.
No business logic. No database queries. No configuration loading.
All of that lives in the appropriate modules.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.logging.middleware import RequestLoggingMiddleware
from app.api.v1.health import router as health_router

# ── Application ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app.name,
    version="1.0.0",
    description=(
        "Production-grade AI platform for knowledge graphs, "
        "GraphRAG++, multi-agent intelligence, root cause analysis, "
        "emergency response, and geospatial intelligence."
    ),
    debug=settings.app.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Middleware ─────────────────────────────────────────────────────────────────
# Order matters: RequestLoggingMiddleware must wrap everything to capture
# the full request/response cycle including CORS and error handling.
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(health_router)                             # GET /health
app.include_router(                                           # GET /api/v1/health
    health_router,
    prefix=settings.app.api_prefix,
)


@app.get("/", tags=["Root"], summary="Application status")
async def root():
    """Return basic application identity and status."""
    return {
        "name": settings.app.name,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.app.environment,
        "docs": "/docs",
    }


# ── Dev runner ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app.debug,
    )
