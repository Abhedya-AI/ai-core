"""
infrastructure/preprocessor.py — Image preprocessing utilities.

Responsibility: transform raw image bytes into a format the model
expects before inference.

Design
──────
• Stateless utility functions — no class needed.
• Uses only stdlib + Pillow (already a transitive dependency of
  ultralytics).  NumPy arrays are prepared here so the detector
  only has to call the model.
• All functions operate synchronously; run in a thread-pool executor
  if called from an async context (image I/O is CPU-bound).

Milestone 1
───────────
Basic validation only.  Milestone 2 adds resize, normalise, and
letterbox functions required by YOLO preprocessing.
"""

from __future__ import annotations

import io
from typing import Any

from app.core.logging import get_logger

log = get_logger("vision.preprocessor")


class ImageValidationError(Exception):
    """Raised when the image bytes cannot be decoded or are invalid."""


def validate_image_bytes(image_bytes: bytes) -> None:
    """
    Validate that image_bytes can be decoded as an image.

    Raises
    ──────
    ImageValidationError  If the bytes are empty or cannot be decoded.
    """
    if not image_bytes:
        raise ImageValidationError("Image bytes are empty.")

    # Check for common image magic bytes
    _MAGIC = {
        b"\xff\xd8\xff":      "JPEG",
        b"\x89PNG\r\n\x1a\n": "PNG",
        b"GIF87a":            "GIF",
        b"GIF89a":            "GIF",
        b"BM":                "BMP",
        b"RIFF":              "WEBP (possible)",
    }
    detected = None
    for magic, fmt in _MAGIC.items():
        if image_bytes[:len(magic)] == magic:
            detected = fmt
            break

    if detected is None:
        log.warning("Image format not recognised from magic bytes — proceeding.")
    else:
        log.debug(f"Image format detected: {detected}")


def get_image_dimensions(image_bytes: bytes) -> tuple[int, int]:
    """
    Return (width, height) of the image without full decode.

    Requires Pillow.

    Raises
    ──────
    ImageValidationError  If Pillow is unavailable or decoding fails.
    """
    try:
        from PIL import Image  # type: ignore[import]
        img = Image.open(io.BytesIO(image_bytes))
        return img.size  # (width, height)
    except ImportError as exc:
        raise ImageValidationError(
            "Pillow is required for image dimension extraction. "
            "Install it with: uv add pillow"
        ) from exc
    except Exception as exc:
        raise ImageValidationError(f"Failed to read image dimensions: {exc}") from exc


def decode_image(image_bytes: bytes) -> Any:
    """
    Decode raw bytes into a PIL Image.

    Returns
    ───────
    PIL.Image.Image

    Raises
    ──────
    ImageValidationError  If decoding fails.
    """
    try:
        from PIL import Image  # type: ignore[import]
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except ImportError as exc:
        raise ImageValidationError(
            "Pillow is required. Install with: uv add pillow"
        ) from exc
    except Exception as exc:
        raise ImageValidationError(f"Failed to decode image: {exc}") from exc


# ── Milestone 2 stubs (uncomment and implement) ───────────────────────────────

# def letterbox(
#     image: "PIL.Image.Image",
#     target_size: tuple[int, int] = (640, 640),
#     fill_color: tuple[int, int, int] = (114, 114, 114),
# ) -> "PIL.Image.Image":
#     """Resize with aspect-ratio preservation and grey padding (YOLO standard)."""
#     ...

# def to_numpy_rgb(image: "PIL.Image.Image") -> "np.ndarray":
#     """Convert a PIL Image to a HWC uint8 NumPy array."""
#     import numpy as np
#     return np.asarray(image)
