"""
vision/infrastructure/detector_factory.py — Detector Factory.

Creates the appropriate BaseDetector implementation based on configuration.
Supports model switching without changing application code.

Supported model_type values:
  - 'stub'           — StubDetector (default, no ML required)
  - 'yolo'           — YOLODetector
  - 'rtdetr'         — RTDETRDetector (import-guarded)
  - 'grounding_dino' — GroundingDINODetector (import-guarded)
"""
from __future__ import annotations
from typing import Any
from app.core.logging import get_logger
from app.modules.vision.infrastructure.detector import BaseDetector, StubDetector

log = get_logger("vision.infrastructure.detector_factory")

SUPPORTED_MODELS = ['stub', 'yolo', 'rtdetr', 'grounding_dino']

class DetectorFactory:
    @staticmethod
    def create(model_type: str = 'stub', model_path: str | None = None, **kwargs) -> BaseDetector:
        model_type = model_type.lower()
        if model_type not in SUPPORTED_MODELS:
            log.warning(f"Unknown model_type '{model_type}', falling back to StubDetector")
            return StubDetector()
            
        if model_type == 'stub':
            return StubDetector()
            
        elif model_type == 'yolo':
            try:
                from app.modules.vision.infrastructure.detectors.yolo_detector import YOLODetector
                return YOLODetector(model_path=model_path, **kwargs)
            except ImportError:
                log.warning("YOLODetector not available, falling back to StubDetector")
                return StubDetector()
                
        elif model_type == 'rtdetr':
            try:
                from app.modules.vision.infrastructure.detectors.rt_detr_detector import RTDETRDetector
                return RTDETRDetector(model_path=model_path, **kwargs)
            except ImportError:
                log.warning("RTDETRDetector not available, falling back to StubDetector")
                return StubDetector()
                
        elif model_type == 'grounding_dino':
            try:
                from app.modules.vision.infrastructure.detectors.grounding_dino_detector import GroundingDINODetector
                return GroundingDINODetector(model_path=model_path, **kwargs)
            except ImportError:
                log.warning("GroundingDINODetector not available, falling back to StubDetector")
                return StubDetector()

        return StubDetector()
