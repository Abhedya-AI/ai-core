"""
infrastructure/__init__.py — Re-exports for the infrastructure layer.
"""

from app.modules.vision.infrastructure.detector import BaseDetector, StubDetector
from app.modules.vision.infrastructure.kafka_publisher import KafkaVisionPublisher
from app.modules.vision.infrastructure.mapper import map_raw_detection, map_raw_detections
from app.modules.vision.infrastructure.model_loader import ModelLoader
from app.modules.vision.infrastructure.postgres_repository import (
    DetectionModel,
    PostgresVisionRepository,
    VisionEventModel,
)
from app.modules.vision.infrastructure.preprocessor import (
    ImageValidationError,
    decode_image,
    get_image_dimensions,
    validate_image_bytes,
)
from app.modules.vision.infrastructure.yolo_detector import YOLODetector

__all__ = [
    # detector
    "BaseDetector",
    "StubDetector",
    "YOLODetector",
    # mapper
    "map_raw_detection",
    "map_raw_detections",
    # model
    "ModelLoader",
    # preprocessor
    "validate_image_bytes",
    "decode_image",
    "get_image_dimensions",
    "ImageValidationError",
    # repository
    "PostgresVisionRepository",
    "VisionEventModel",
    "DetectionModel",
    # kafka
    "KafkaVisionPublisher",
]
