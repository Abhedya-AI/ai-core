"""
vision/infrastructure/detectors/rt_detr_detector.py
"""
from __future__ import annotations
from app.modules.vision.infrastructure.detector import BaseDetector

class RTDETRDetector(BaseDetector):
    def __init__(self, model_name: str = 'rt-detr-l', model_path: str | None = None, **kwargs):
        self.model_name = model_name
        self.model_path = model_path
        
    async def detect(self, image: bytes) -> list[dict]:
        raise ImportError("RT-DETR not installed")
