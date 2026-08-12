"""
application/dto/__init__.py
"""

from .analyze_request import AnalyzeFrameRequest
from .analyze_response import FrameAnalysisResult

__all__ = [
    "AnalyzeFrameRequest",
    "FrameAnalysisResult",
]
