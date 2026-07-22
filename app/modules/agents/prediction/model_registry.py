"""model_registry.py — Plug-and-play Prediction Model Registry."""

from typing import Any

from app.core.logging import get_logger
from app.modules.agents.prediction.providers import (
    EnvironmentalRiskModel,
    EquipmentFailureModel,
    IncidentPredictionModel,
    MaintenanceForecastModel,
    OccupancyForecastModel,
)

log = get_logger("agents.prediction.registry")


class PredictionModelRegistry:
    """Registry singleton managing plug-and-play predictive model providers."""

    _instance: "PredictionModelRegistry | None" = None

    def __init__(self) -> None:
        self._models: dict[str, Any] = {}
        # Auto-register default model providers
        self.register(EquipmentFailureModel.model_name, EquipmentFailureModel())
        self.register(IncidentPredictionModel.model_name, IncidentPredictionModel())
        self.register(MaintenanceForecastModel.model_name, MaintenanceForecastModel())
        self.register(OccupancyForecastModel.model_name, OccupancyForecastModel())
        self.register(EnvironmentalRiskModel.model_name, EnvironmentalRiskModel())

    @classmethod
    def get(cls) -> "PredictionModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, name: str, model_provider: Any) -> None:
        """Register a predictive model provider."""
        self._models[name.lower()] = model_provider
        log.info(f"Registered prediction model provider: '{name}'")

    def get_model(self, name: str) -> Any | None:
        """Get registered model provider by name."""
        return self._models.get(name.lower())

    def list_models(self) -> list[str]:
        """List names of all registered model providers."""
        return list(self._models.keys())
