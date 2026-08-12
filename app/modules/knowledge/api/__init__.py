"""
api/__init__.py — Knowledge Module API Package.
"""
from app.modules.knowledge.api.routes import router as knowledge_router
from app.modules.knowledge.api.ws import router as knowledge_ws_router

__all__ = ["knowledge_router", "knowledge_ws_router"]
