"""
ABHEDYA AI Core — application entry point.

Responsibility: assemble the FastAPI application only.
No business logic lives here.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config.settings import settings, security
from app.core.lifespan import lifespan
from app.api.v1.health import router as health_router

# ── Application ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Production-grade AI platform for knowledge graphs, GraphRAG, and multi-agent intelligence.",
    debug=settings.app_debug,
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=security.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(health_router)                                        # GET /health
app.include_router(health_router, prefix=f"/api/{settings.api_version}") # GET /api/v1/health


@app.get("/", tags=["Root"], summary="Application status")
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.app_env,
        "docs": "/docs",
    }


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_debug,
    )
