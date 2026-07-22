"""
infrastructure/model_loader.py — Model loading and caching.

Responsibility: load the vision model once at startup and serve the
same instance for every inference request.

Design
──────
• Uses a module-level dict as a process-wide model cache.
• Thread-safe for read access; write access (load) happens once at
  startup before request handling begins.
• Decoupled from the detector class so multiple detectors can share
  the same loader infrastructure.
• In Milestone 1 this is a stub; Milestone 2 wires in the real
  ultralytics YOLO model.

Usage
─────
    from app.modules.vision.infrastructure.model_loader import ModelLoader

    loader = ModelLoader()
    model  = await loader.get("yolov11n.pt")   # loads once, cached
    model  = await loader.get("yolov11n.pt")   # returns cached instance
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

log = get_logger("vision.model_loader")

# ── Model cache ───────────────────────────────────────────────────────────────
# Key: model path string.  Value: loaded model object.
_MODEL_CACHE: dict[str, Any] = {}
_CACHE_LOCK = asyncio.Lock()


class ModelLoader:
    """
    Process-wide model cache.

    All instances share the same underlying cache dict.
    """

    async def get(self, model_path: str) -> Any:
        """
        Return the cached model, loading it if necessary.

        Parameters
        ──────────
        model_path  Path to the model weights file (relative or absolute).

        Returns
        ───────
        The loaded model object.  The concrete type depends on the
        framework (e.g. ultralytics.YOLO for YOLO models).

        Raises
        ──────
        ModelLoadError  If the model file cannot be loaded.
        """
        async with _CACHE_LOCK:
            if model_path in _MODEL_CACHE:
                log.debug(f"Model cache hit: {model_path}")
                return _MODEL_CACHE[model_path]

            log.info(f"Loading model: {model_path}")
            model = await self._load(model_path)
            _MODEL_CACHE[model_path] = model
            log.info(f"Model loaded and cached: {model_path}")
            return model

    async def _load(self, model_path: str) -> Any:
        """
        Internal loading logic.  Override or replace in concrete loaders.

        Milestone 1: returns a sentinel string (stub).
        Milestone 2: uncomment the ultralytics block.
        """
        # ── Milestone 2: real YOLO loading ────────────────────────────────────
        # import asyncio
        # from ultralytics import YOLO
        # loop = asyncio.get_event_loop()
        # model = await loop.run_in_executor(None, YOLO, model_path)
        # return model
        # ─────────────────────────────────────────────────────────────────────

        # Milestone 1 stub — returns a placeholder
        log.warning(
            f"ModelLoader: real loading not yet wired (Milestone 1 stub). "
            f"Model path={model_path}"
        )
        return f"stub-model:{model_path}"

    def invalidate(self, model_path: str) -> None:
        """Remove a specific model from the cache (useful for hot-reloading)."""
        if model_path in _MODEL_CACHE:
            del _MODEL_CACHE[model_path]
            log.info(f"Model cache invalidated: {model_path}")

    def clear(self) -> None:
        """Flush the entire model cache."""
        _MODEL_CACHE.clear()
        log.info("Model cache cleared.")

    @property
    def cached_models(self) -> list[str]:
        """List of currently cached model paths."""
        return list(_MODEL_CACHE.keys())


# ── Error ─────────────────────────────────────────────────────────────────────

class ModelLoadError(Exception):
    """Raised when a model cannot be loaded."""
