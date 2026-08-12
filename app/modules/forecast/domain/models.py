from __future__ import annotations
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.modules.forecast.domain.enums import (
    ForecastHorizon, ForecastType, ForecastStatus, ScenarioType,
    ConfidenceLevel, ModelFamily, ForecastTrend, RecommendationType,
    ForecastTarget, UncertaintySource
)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uuid() -> str:
    return str(uuid.uuid4())

class ForecastConfidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    overall: float
    data_completeness: float
    model_confidence: float
    historical_coverage: float
    graphrag_coverage: float

    @property
    def is_reliable(self) -> bool:
        return self.overall >= 0.6

    @property
    def level(self) -> ConfidenceLevel:
        return ConfidenceLevel.from_score(self.overall)

class ForecastWindow(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    start: str
    end: str
    horizon: ForecastHorizon
    duration_minutes: int

    @classmethod
    def for_horizon(cls, horizon: ForecastHorizon) -> ForecastWindow:
        now = datetime.now(timezone.utc)
        duration = horizon.minutes
        end_time = now + timedelta(minutes=duration)
        return cls(
            start=now.isoformat(),
            end=end_time.isoformat(),
            horizon=horizon,
            duration_minutes=duration
        )

    @property
    def midpoint_iso(self) -> str:
        start_dt = datetime.fromisoformat(self.start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(self.end.replace("Z", "+00:00"))
        midpoint = start_dt + (end_dt - start_dt) / 2
        return midpoint.isoformat()

class ForecastMetric(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    value: float
    unit: str
    threshold: float
    is_breached: bool
    trend: ForecastTrend

    @property
    def severity_score(self) -> float:
        if self.threshold == 0:
            return 0.0
        ratio = self.value / self.threshold
        return min(max(ratio, 0.0), 1.0) if not self.is_breached else min(ratio, 10.0)

class ForecastEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    evidence_id: str = Field(default_factory=_uuid)
    source: str
    content: str
    confidence: float
    citations: list[str]
    evidence_type: str

class ForecastTimeline(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    entity_id: str
    target: ForecastTarget
    entries: list[dict[str, Any]]
    window_hours: int
    generated_at: str = Field(default_factory=_now_iso)

class ForecastExplanation(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    explanation_id: str = Field(default_factory=_uuid)
    methodology: str
    feature_importance: dict[str, float]
    historical_evidence: list[str]
    kg_paths: list[str]
    graphrag_citations: list[str]
    risk_references: list[str]
    rca_references: list[str]
    uncertainty_factors: list[UncertaintySource]
    uncertainty_score: float
    confidence_intervals: dict[str, list[float]]  # horizon -> [lower, upper]
    recommended_actions: list[str]

class ForecastRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    recommendation_id: str = Field(default_factory=_uuid)
    recommendation_type: RecommendationType
    priority: str
    title: str
    description: str
    rationale: str
    kg_node_refs: list[str]
    graphrag_citations: list[str]
    risk_refs: list[str]
    rca_refs: list[str]
    estimated_impact: float
    time_to_implement: str
    resources_required: list[str]
    applies_to: list[str]
    generated_at: str = Field(default_factory=_now_iso)

class Forecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    forecast_id: str = Field(default_factory=_uuid)
    entity_id: str
    entity_type: ForecastTarget
    forecast_type: ForecastType
    window: ForecastWindow
    status: ForecastStatus
    model_family: ModelFamily
    current_value: float
    predicted_value: float
    confidence: ForecastConfidence
    trend: ForecastTrend
    explanation: ForecastExplanation | None
    metrics: list[ForecastMetric]
    evidence: list[ForecastEvidence]
    generated_at: str = Field(default_factory=_now_iso)
    valid_until: str

    @property
    def health_score(self) -> float:
        return max(0.0, min(1.0, 1.0 - self.predicted_value))

    @property
    def requires_action(self) -> bool:
        return self.trend in (ForecastTrend.DEGRADING, ForecastTrend.VOLATILE) or self.predicted_value > 0.8

class ForecastResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    result_id: str = Field(default_factory=_uuid)
    entity_id: str
    entity_type: ForecastTarget
    forecast_type: ForecastType
    horizons: dict[str, Forecast]
    recommendations: list[ForecastRecommendation]
    explanation: ForecastExplanation
    generated_at: str = Field(default_factory=_now_iso)
    latency_ms: int

    @property
    def peak_forecast(self) -> Forecast | None:
        if not self.horizons:
            return None
        return max(self.horizons.values(), key=lambda f: f.predicted_value)

class ForecastScenario(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    scenario_id: str = Field(default_factory=_uuid)
    scenario_type: ScenarioType
    entity_id: str
    entity_type: ForecastTarget
    forecast_type: ForecastType
    horizon: ForecastHorizon
    predicted_value: float
    confidence: float
    probability: float
    conditions: dict[str, Any]
    description: str
    key_drivers: list[str]
    generated_at: str = Field(default_factory=_now_iso)

class ForecastComparison(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    comparison_id: str = Field(default_factory=_uuid)
    entity_id: str
    forecast_type: ForecastType
    horizon: ForecastHorizon
    best_case: ForecastScenario
    expected_case: ForecastScenario
    worst_case: ForecastScenario
    generated_at: str = Field(default_factory=_now_iso)

    @property
    def spread(self) -> float:
        return max(0.0, self.worst_case.predicted_value - self.best_case.predicted_value)

    @property
    def uncertainty_score(self) -> float:
        return self.spread * (1.0 - self.expected_case.confidence)

    @property
    def recommended_scenario(self) -> ScenarioType:
        scenarios = [self.best_case, self.expected_case, self.worst_case]
        return max(scenarios, key=lambda s: s.probability).scenario_type

class EquipmentForecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    base: ForecastResult
    equipment_id: str
    equipment_type: str
    equipment_name: str
    health_score: float
    degradation_rate: float
    rul_hours: float | None
    failure_probability: dict[str, float]
    maintenance_urgency: str
    anomalous_sensors: list[str]
    next_maintenance_window: str | None

class WorkerForecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    base: ForecastResult
    worker_id: str
    worker_role: str
    current_zone_id: str
    safety_score: float
    exposure_risk_score: float
    fatigue_index: float
    ppe_compliance_forecast: float
    recommended_actions: list[str]

class ZoneForecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    base: ForecastResult
    zone_id: str
    zone_name: str
    hazard_probability: dict[str, float]
    worker_exposure_score: float
    equipment_risk_score: float
    environmental_risk_score: float
    occupancy_forecast: int

class PlantForecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    base: ForecastResult
    plant_id: str
    plant_name: str
    overall_health_score: float
    operational_stability_score: float
    emergency_readiness_score: float
    compliance_score: float
    critical_zones: list[str]
    critical_equipment: list[str]
    zone_forecasts: list[ZoneForecast]

class HazardForecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    base: ForecastResult
    hazard_id: str
    hazard_type: str
    propagation_path: list[str]
    affected_zones: list[str]
    affected_workers_estimate: int
    containment_probability: float
    escalation_probability: float

class EnvironmentalForecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    base: ForecastResult
    zone_id: str
    temperature_forecast: dict[str, float]
    humidity_forecast: dict[str, float]
    gas_concentration_forecast: dict[str, float]
    air_quality_index_forecast: dict[str, float]
    dust_level_forecast: dict[str, float]
    noise_forecast: dict[str, float]
    threshold_breaches: list[dict[str, Any]]

class ResourceForecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    base: ForecastResult
    worker_availability: dict[str, int]
    equipment_utilization: dict[str, float]
    safety_personnel_demand: dict[str, int]
    maintenance_crew_demand: dict[str, int]
    energy_consumption_kwh: dict[str, float]
    water_usage_liters: dict[str, float]
    fuel_demand_liters: dict[str, float]

class MaintenanceForecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    base: ForecastResult
    equipment_id: str
    equipment_type: str
    degradation_curve: list[dict[str, Any]]
    predicted_failure_window: dict[str, Any] | None
    rul_hours: float | None
    rul_confidence: float
    maintenance_schedule: list[dict[str, Any]]
    replacement_recommendations: list[str]
    inspection_intervals: dict[str, int]
    maintenance_backlog_hours: float

class CapacityForecast(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    base: ForecastResult
    production_capacity_pct: dict[str, float]
    resource_sufficiency: dict[str, bool]
    bottleneck_equipment: list[str]
    bottleneck_zones: list[str]
    recommended_capacity_actions: list[str]
