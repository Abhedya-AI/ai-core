"""
infrastructure/detector.py — Common detector interface (port).

All concrete detector implementations must satisfy this interface.
The application layer depends on this abstract class, not on YOLO.

Concrete implementations (Milestone 2+):
    yolo_detector.py      — YOLOv11 implementation
    (future) rtdetr_detector.py
    (future) grounding_dino_detector.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.vision.domain.entities import Detection


class BaseDetector(ABC):
    """
    Abstract base class for all vision detectors.

    Implementations are responsible for:
      1. Loading and caching the model (via model_loader.py).
      2. Pre-processing the image (via preprocessor.py).
      3. Running inference.
      4. Mapping raw outputs to domain Detections (via mapper.py).
      5. Filtering by min_confidence.
    """

    @abstractmethod
    async def detect(
        self,
        image_bytes: bytes,
        frame_id: str,
        camera_id: str,
        min_confidence: float = 0.4,
    ) -> list[Detection]:
        """
        Run inference on image_bytes and return domain Detections.

        Parameters
        ──────────
        image_bytes     Raw image bytes (JPEG, PNG, etc.).
        frame_id        Caller-assigned frame identifier.
        camera_id       Source camera identifier.
        min_confidence  Drop detections below this threshold.

        Returns
        ───────
        List of domain Detection objects (may be empty).
        """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return a human-readable model identifier for logging."""

    async def warm_up(self) -> None:
        """
        Optional warm-up hook called at application startup.

        Override in concrete implementations to pre-load the model
        and run a dummy inference so the first real request is fast.
        Default implementation is a no-op.
        """


# ── Stub implementation (Milestone 1) ─────────────────────────────────────────

class StubDetector(BaseDetector):
    """
    No-op detector used in Milestone 1 before YOLO is wired.

    Returns an empty detection list.  The pipeline still executes fully
    (risk engine, repository, Kafka) with zero detections.

    Replace with YOLODetector in Milestone 2.
    """

    @property
    def model_name(self) -> str:
        return "stub-detector-v0"

    async def detect(
        self,
        image_bytes: bytes,
        frame_id: str,
        camera_id: str,
        min_confidence: float = 0.4,
    ) -> list[Detection]:
        return []
