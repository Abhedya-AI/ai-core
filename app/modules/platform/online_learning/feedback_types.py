from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import Any
from datetime import datetime, timezone
import uuid

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uuid() -> str:
    return str(uuid.uuid4())

class BaseFeedback(BaseModel):
    model_config = ConfigDict(frozen=True)
    feedback_id: str = Field(default_factory=_uuid)
    model_id: str
    entity_id: str
    entity_type: str
    prediction: float  # original prediction
    actual: float | None = None  # ground truth if available
    confidence: float
    error: float | None = None  # |actual - prediction| if actual known
    feedback_source: str  # "human", "sensor", "simulation"
    submitted_at: str = Field(default_factory=_now_iso)
    tenant_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

class RiskFeedback(BaseFeedback):
    model_config = ConfigDict(frozen=True)
    risk_type: str
    risk_level: str  # actual risk level observed
    incident_occurred: bool = False

class ForecastFeedback(BaseFeedback):
    model_config = ConfigDict(frozen=True)
    forecast_type: str
    horizon: str
    actual_at_horizon: float | None = None

class HazardFeedback(BaseFeedback):
    model_config = ConfigDict(frozen=True)
    hazard_type: str
    propagation_occurred: bool = False
    affected_zones: list[str] = Field(default_factory=list)

class RCAFeedback(BaseFeedback):
    model_config = ConfigDict(frozen=True)
    predicted_root_cause: str
    actual_root_cause: str | None = None
    cause_matched: bool = False

class TwinFeedback(BaseFeedback):
    model_config = ConfigDict(frozen=True)
    twin_id: str
    simulation_type: str
    actual_outcome: dict[str, Any] = Field(default_factory=dict)
    simulation_accuracy: float | None = None

class SimulationFeedback(BaseFeedback):
    model_config = ConfigDict(frozen=True)
    simulation_id: str
    simulation_type: str
    divergence_score: float = 0.0  # 0=perfect, 1=completely wrong
    actual_timeline: list[dict[str, Any]] = Field(default_factory=list)
