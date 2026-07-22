"""
api/__init__.py — Re-exports the vision API router.
"""

from app.modules.vision.api.routes import router

__all__ = ["router"]
