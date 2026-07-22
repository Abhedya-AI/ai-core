"""inference.py — Model Inference Execution Engine."""

import time
from typing import Any

from app.core.logging import get_logger
from app.modules.agents.prediction.model_registry import PredictionModelRegistry
from app.modules.agents.prediction.models import PredictionFeatures, PredictionOutput, PredictionWindow

log = get_logger("agents.prediction.inference")


class ModelInferenceEngine:
    """Executes prediction model inference with feature validation and timing telemetry."""

    def __init__(self, registry: PredictionModelRegistry | None = None) -> None:
        self.registry = registry or PredictionModelRegistry.get()

    def run_inference(self, model_name: str, features: PredictionFeatures, window: PredictionWindow) -> PredictionOutput | None:
        """
        Run inference using named model provider.

        Returns:
            PredictionOutput or None if model provider not registered.
        """
        start = time.perf_counter()
        model = self.registry.get_model(model_name)
        if not model:
            log.warning(f"Prediction model provider '{model_name}' not registered")
            return None

        output = model.predict(features, window)
        latency = int((time.perf_counter() - start) * 1000)
        output.metadata["inference_latency_ms"] = latency
        log.info(f"Model '{model_name}' inference finished in {latency}ms (prob={output.probability:.2f})")
        return output
