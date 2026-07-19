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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.allowed_origins,
    allow_credentials=settings.security.allow_credentials,
    allow_methods=settings.security.allowed_methods,
    allow_headers=settings.security.allowed_headers,
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
        "environment": settings.app.env,
        "docs": "/docs",
    }


# ── Dev runner ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
