"""
infrastructure/yolo_detector.py — YOLOv11 detector implementation.

Milestone 1: Skeleton class with full interface — no model loaded.
Milestone 2: Uncomment the ultralytics import and inference block.

This class:
  1. Uses ModelLoader to load the YOLO model once.
  2. Uses preprocessor.py to decode and resize the image.
  3. Runs YOLO inference.
  4. Uses mapper.py to convert raw boxes → domain Detections.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.domain.entities import Detection
from app.modules.vision.infrastructure.detector import BaseDetector
from app.modules.vision.infrastructure.mapper import map_raw_detections
from app.modules.vision.infrastructure.model_loader import ModelLoader
from app.modules.vision.infrastructure.preprocessor import (
    ImageValidationError,
    validate_image_bytes,
)

log = get_logger("vision.yolo_detector")

# Default model weights path (relative to project root or absolute)
DEFAULT_MODEL_PATH = "datasets/models/yolov11n.pt"


class YOLODetector(BaseDetector):
    """
    YOLO-based detector implementation.

    Constructor
    ───────────
    model_path      Path to YOLO weights file.
    device          Inference device: "cpu", "cuda", "mps".
    loader          ModelLoader instance (injected for testability).

    Usage
    ─────
        detector = YOLODetector(model_path="yolov11n.pt", device="cpu")
        detections = await detector.detect(image_bytes, frame_id, camera_id)
    """

    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        device:     str = "cpu",
        loader:     ModelLoader | None = None,
    ) -> None:
        self._model_path = model_path
        self._device     = device
        self._loader     = loader or ModelLoader()
        self._model      = None   # loaded lazily via warm_up() or first detect()

    @property
    def model_name(self) -> str:
        return f"yolo:{self._model_path}"

    async def warm_up(self) -> None:
        """Pre-load the model at startup."""
        self._model = await self._loader.get(self._model_path)
        log.info(f"YOLODetector warmed up: {self._model_path} on {self._device}")

    async def detect(
        self,
        image_bytes:    bytes,
        frame_id:       str,
        camera_id:      str,
        min_confidence: float = 0.4,
    ) -> list[Detection]:
        """
        Run YOLO inference and return domain Detections.

        Milestone 1: validates the image and returns [].
        Milestone 2: uncomment the inference block below.
        """
        try:
            validate_image_bytes(image_bytes)
        except ImageValidationError as exc:
            log.warning(f"Image validation failed: {exc}")
            return []

        # Ensure model is loaded
        if self._model is None:
            self._model = await self._loader.get(self._model_path)

        # ── Milestone 2: real inference ────────────────────────────────────────
        # import asyncio
        # from PIL import Image
        # import io
        #
        # pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # img_w, img_h = pil_image.size
        #
        # loop = asyncio.get_event_loop()
        # results = await loop.run_in_executor(
        #     None,
        #     lambda: self._model.predict(
        #         source=pil_image,
        #         conf=min_confidence,
        #         device=self._device,
        #         verbose=False,
        #     )
        # )
        #
        # raw_detections = []
        # for result in results:
        #     boxes = result.boxes
        #     for i in range(len(boxes)):
        #         x1, y1, x2, y2 = boxes.xyxy[i].tolist()
        #         conf  = float(boxes.conf[i])
        #         cls   = int(boxes.cls[i])
        #         label = result.names[cls]
        #         raw_detections.append({
        #             "class_name":   label,
        #             "confidence":   conf,
        #             "x1": int(x1), "y1": int(y1),
        #             "x2": int(x2), "y2": int(y2),
        #             "image_width":  img_w,
        #             "image_height": img_h,
        #         })
        #
        # return map_raw_detections(
        #     raw_detections, frame_id, camera_id,
        #     min_confidence=min_confidence,
        # )
        # ─────────────────────────────────────────────────────────────────────

        # Milestone 1: return empty list
        log.debug(
            f"YOLODetector (M1 stub): image validated, returning [] "
            f"frame_id={frame_id} camera_id={camera_id}"
        )
        return []
