"""
vision/infrastructure/detectors/grounding_dino_detector.py
"""
from __future__ import annotations
from app.modules.vision.infrastructure.detector import BaseDetector

class GroundingDINODetector(BaseDetector):
    def __init__(self, model_path: str | None = None, text_prompt: str = "", **kwargs):
        self.model_path = model_path
        self.text_prompt = text_prompt
        
    async def detect(self, image: bytes) -> list[dict]:
        raise ImportError("GroundingDINO not installed")
