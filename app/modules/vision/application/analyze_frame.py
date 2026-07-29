"""
application/analyze_frame.py — backward-compatibility shim.

The canonical implementation is now at:
    application/use_cases/analyze_frame.py

This file re-exports everything so existing imports keep working
without modification during the transition.
"""

from app.modules.vision.application.use_cases.analyze_frame import (
    AnalyzeFrameUseCase,
    FrameDetector,
)

__all__ = [
    "AnalyzeFrameUseCase",
    "FrameDetector",
]
