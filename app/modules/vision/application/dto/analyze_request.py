"""
application/dto/analyze_request.py — Application-layer request DTO.

This re-exports AnalyzeFrameRequest from the schemas layer so the
application use cases are decoupled from the FastAPI schema location.

If the schema ever moves or is replaced by a different transport format
(gRPC, CLI, background job), only this file changes — not the use cases.
"""

from app.modules.vision.schemas.request import AnalyzeFrameRequest

__all__ = ["AnalyzeFrameRequest"]
