from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Any

try:
    from app.core.logging import get_logger
    log = get_logger(__name__)
except ImportError:
    log = logging.getLogger(__name__)

@dataclass
class ForecastModelResult:
    predicted_values: list[float]
    confidence_lower: list[float]
    confidence_upper: list[float]
    confidence_score: float
    feature_importance: dict[str, float]
    model_family: str
    methodology: str
    uncertainty_score: float
    metadata: dict[str, Any] = field(default_factory=dict)

@runtime_checkable
class AbstractForecastModel(Protocol):
    async def train(self, time_series: list[float], timestamps: list[str]) -> None:
        """Trains the forecast model."""
        ...
        
    async def forecast(self, steps: int, context: dict[str, Any]) -> ForecastModelResult:
        """Generates a forecast for the specified number of steps."""
        ...
        
    def confidence(self) -> float:
        """Returns the overall confidence of the trained model (0.0 to 1.0)."""
        ...
        
    def explain(self) -> dict[str, Any]:
        """Provides an explanation of the model's internal state and feature importances."""
        ...
        
    def serialize(self) -> dict[str, Any]:
        """Serializes the model state to a dictionary."""
        ...

class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, type[AbstractForecastModel]] = {}
        
    def register(self, name: str, model_cls: type[AbstractForecastModel]) -> None:
        self._models[name] = model_cls
        log.info(f"Registered model: {name}")
        
    def get(self, name: str) -> type[AbstractForecastModel]:
        if name not in self._models:
            raise KeyError(f"Model {name} not found in registry.")
        return self._models[name]
        
    def list_models(self) -> list[str]:
        return list(self._models.keys())
