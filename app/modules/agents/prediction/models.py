"""models.py — Prediction Agent Domain Models & DTOs."""

from typing import Any

from pydantic import BaseModel, Field

from app.modules.agents.core.agent_result import AgentResult


class PredictionWindow(BaseModel):
    """Forecast time horizon representation."""

    horizon_hours: float = Field(default=24.0, description="Horizon duration in hours")
    horizon_label: str = Field(default="24h", description="e.g. 15m, 1h, 6h, 24h, 7d, 30d")


class PredictionFeatures(BaseModel):
    """Extracted numeric & categorical features for model consumption."""

    target_entity_id: str
    sensor_vibration_delta_pct: float = 0.0
    sensor_temp_c: float = 25.0
    maintenance_overdue_days: int = 0
    operating_hours: float = 1000.0
    incident_history_count: int = 0
    vision_anomalies_count: int = 0
    feature_vector: list[float] = Field(default_factory=list)


class PredictionConfidence(BaseModel):
    """Multi-factor prediction confidence metrics."""

    model_confidence: float = 0.90
    data_completeness: float = 0.95
    feature_freshness: float = 0.98
    sensor_quality: float = 0.92
    overall_confidence: float = 0.93


class PredictionOutput(BaseModel):
    """Standardized output produced by a predictive model provider."""

    target_entity_id: str
    prediction_type: str = Field(..., description="EQUIPMENT_FAILURE, INCIDENT_PROBABILITY, etc.")
    probability: float = Field(..., ge=0.0, le=1.0)
    remaining_useful_life_days: float | None = None
    prediction_window: PredictionWindow = Field(default_factory=PredictionWindow)
    confidence: PredictionConfidence = Field(default_factory=PredictionConfidence)
    feature_importances: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PredictionAgentResult(AgentResult):
    """Domain-extended result returned by Predictive Intelligence Agent."""

    predictions: list[PredictionOutput] = Field(default_factory=list)
    forecast_horizons: list[str] = Field(default_factory=list)
    recommended_actions: dict[str, list[str]] = Field(default_factory=dict)
    feature_explanations: list[str] = Field(default_factory=list)
