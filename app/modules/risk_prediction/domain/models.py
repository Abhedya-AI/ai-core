"""
app/modules/risk_prediction/domain/models.py — Risk Prediction core domain models.

All domain entities are immutable Pydantic v2 models.
These are the authoritative data contracts for the Predictive Risk Intelligence Platform.

Design principles:
  - Frozen models for thread-safety across async prediction pipeline
  - Rich computed properties for risk level classification
  - All timestamps UTC ISO-8601
  - Confidence scores follow 0.0-1.0 convention
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.modules.risk_prediction.domain.enums import (
    AssessmentStatus,
    EntityType,
    FeatureCategory,
    ForecastHorizon,
    MitigationPriority,
    MitigationType,
    ModelType,
    RiskLevel,
    RiskType,
    TrendDirection,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Value Objects ──────────────────────────────────────────────────────────────


class RiskScore(BaseModel):
    """Atomic risk score with classification and uncertainty.

    Attributes:
        value:       Probability 0.0 (safe) → 1.0 (certain failure).
        level:       Categorical classification derived from value.
        confidence:  Model confidence in this score (0.0-1.0).
        uncertainty: Epistemic uncertainty (std of ensemble predictions).
    """

    model_config = ConfigDict(frozen=True)

    value: float = Field(..., ge=0.0, le=1.0, description="Risk probability [0,1]")
    level: RiskLevel = Field(..., description="Categorical risk classification")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)

    @classmethod
    def from_probability(
        cls,
        probability: float,
        confidence: float = 1.0,
        uncertainty: float = 0.0,
    ) -> "RiskScore":
        """Construct a RiskScore from a raw probability."""
        prob = max(0.0, min(1.0, probability))
        return cls(
            value=prob,
            level=RiskLevel.from_probability(prob),
            confidence=confidence,
            uncertainty=uncertainty,
        )

    @property
    def is_elevated(self) -> bool:
        """True if risk is HIGH or above."""
        return self.level in (RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EXTREME)

    @property
    def requires_immediate_action(self) -> bool:
        """True if risk requires immediate intervention."""
        return self.level in (RiskLevel.CRITICAL, RiskLevel.EXTREME)


class RiskFactor(BaseModel):
    """A single contributing factor to a risk score.

    Each factor explains a portion of the total risk probability
    via its weight and contribution values.
    """

    model_config = ConfigDict(frozen=True)

    factor_id: str = Field(default_factory=_uuid)
    name: str = Field(..., description="Human-readable factor name")
    weight: float = Field(..., ge=0.0, le=1.0, description="Model weight for this factor")
    contribution: float = Field(..., description="Signed contribution to risk score")
    category: FeatureCategory = Field(..., description="Feature source category")
    description: str = Field(default="", description="Explanation of this factor")
    feature_value: float | None = Field(default=None, description="Raw feature value")


class RiskFeature(BaseModel):
    """A single engineered feature used in risk prediction."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Feature name (e.g. 'sensor_temperature_rolling_mean')")
    value: float = Field(..., description="Normalized feature value")
    raw_value: Any = Field(default=None, description="Original un-normalized value")
    category: FeatureCategory = Field(..., description="Feature source category")
    timestamp: str = Field(default_factory=_now_iso)
    source: str = Field(default="", description="Source identifier (sensor_id, camera_id, etc.)")
    missing: bool = Field(default=False, description="True if feature was imputed/missing")


class RiskEvidence(BaseModel):
    """Supporting evidence for a risk prediction from any intelligence source."""

    model_config = ConfigDict(frozen=True)

    evidence_id: str = Field(default_factory=_uuid)
    source: str = Field(..., description="Evidence source module name")
    content: str = Field(..., description="Evidence summary text")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    citations: list[str] = Field(default_factory=list, description="Document/node citations")
    timestamp: str = Field(default_factory=_now_iso)
    evidence_type: str = Field(default="", description="SENSOR/VISION/GRAPH/GRAPHRAG/RCA")


class RiskConfidence(BaseModel):
    """Composite confidence breakdown across all feature sources.

    Reflects data completeness and quality across all intelligence sources.
    Used for calibration and uncertainty estimation.
    """

    model_config = ConfigDict(frozen=True)

    overall: float = Field(..., ge=0.0, le=1.0, description="Aggregated confidence")
    sensor_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    vision_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    graph_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    graphrag_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    feature_count: int = Field(default=0, description="Total features used")
    missing_feature_count: int = Field(default=0)

    @property
    def completeness_ratio(self) -> float:
        """Ratio of available vs expected features."""
        if self.feature_count == 0:
            return 0.0
        return 1.0 - (self.missing_feature_count / self.feature_count)


class RiskWindow(BaseModel):
    """Temporal window for a risk prediction."""

    model_config = ConfigDict(frozen=True)

    start: str = Field(default_factory=_now_iso)
    end: str = Field(default="", description="Forecast end timestamp")
    horizon: ForecastHorizon = Field(..., description="Prediction horizon")
    duration_minutes: int = Field(..., gt=0)

    @classmethod
    def for_horizon(cls, horizon: ForecastHorizon) -> "RiskWindow":
        """Build a RiskWindow starting now for the given horizon."""
        from datetime import timedelta

        start_dt = datetime.now(timezone.utc)
        end_dt = start_dt + timedelta(minutes=horizon.minutes)
        return cls(
            start=start_dt.isoformat(),
            end=end_dt.isoformat(),
            horizon=horizon,
            duration_minutes=horizon.minutes,
        )


class RiskTrend(BaseModel):
    """Temporal trend in risk level over a sliding window."""

    model_config = ConfigDict(frozen=True)

    direction: TrendDirection = Field(..., description="INCREASING/DECREASING/STABLE/VOLATILE")
    slope: float = Field(..., description="Rate of change in risk score per minute")
    magnitude: float = Field(..., ge=0.0, le=1.0, description="Absolute change magnitude")
    window_minutes: int = Field(..., gt=0, description="Analysis window in minutes")
    r_squared: float = Field(default=0.0, ge=0.0, le=1.0, description="Trend fit quality")


# ── Core Prediction Models ─────────────────────────────────────────────────────


class RiskPrediction(BaseModel):
    """Single risk prediction for one risk type at one time horizon.

    Combines risk score, contributing factors, supporting evidence,
    confidence breakdown, and explanation into a unified output.
    """

    model_config = ConfigDict(frozen=True)

    prediction_id: str = Field(default_factory=_uuid)
    risk_type: RiskType = Field(..., description="Type of risk being predicted")
    risk_score: RiskScore = Field(..., description="Predicted risk score")
    factors: list[RiskFactor] = Field(default_factory=list, description="Top contributing factors")
    evidence: list[RiskEvidence] = Field(default_factory=list, description="Supporting evidence")
    confidence: RiskConfidence = Field(..., description="Prediction confidence breakdown")
    window: RiskWindow = Field(..., description="Temporal prediction window")
    model_type: ModelType = Field(default=ModelType.ENSEMBLE)
    features_used: list[str] = Field(default_factory=list)
    explanation: str = Field(default="", description="Human-readable prediction explanation")
    alternative_outcomes: list[dict[str, Any]] = Field(
        default_factory=list, description="Alternative risk scenarios with probabilities"
    )
    shap_values: dict[str, float] = Field(
        default_factory=dict, description="Feature importance via SHAP abstraction"
    )
    generated_at: str = Field(default_factory=_now_iso)


class RiskForecast(BaseModel):
    """Multi-horizon risk forecast for a single entity.

    Contains predictions across all 7 time horizons (5m → 7d)
    keyed by ForecastHorizon value.
    """

    model_config = ConfigDict(frozen=True)

    forecast_id: str = Field(default_factory=_uuid)
    entity_id: str = Field(..., description="Zone/Equipment/Worker/Plant ID")
    entity_type: EntityType = Field(..., description="Type of entity being assessed")
    predictions: dict[str, RiskPrediction] = Field(
        default_factory=dict, description="Horizon → RiskPrediction mapping"
    )
    generated_at: str = Field(default_factory=_now_iso)
    valid_until: str = Field(default="", description="Forecast expiry timestamp")
    trend: RiskTrend | None = Field(default=None, description="Overall risk trend")
    dominant_risk_type: RiskType | None = Field(
        default=None, description="Highest probability risk type"
    )

    def get_horizon(self, horizon: ForecastHorizon) -> RiskPrediction | None:
        """Get prediction for a specific horizon."""
        return self.predictions.get(horizon.value)

    @property
    def peak_risk(self) -> RiskScore | None:
        """Highest risk score across all horizons."""
        if not self.predictions:
            return None
        return max(
            (p.risk_score for p in self.predictions.values()),
            key=lambda s: s.value,
        )


# ── Recommendation & Mitigation Models ────────────────────────────────────────


class RiskRecommendation(BaseModel):
    """A single actionable mitigation recommendation.

    Cross-referenced with Knowledge Graph nodes, GraphRAG citations,
    and Root Cause Analysis findings.
    """

    model_config = ConfigDict(frozen=True)

    recommendation_id: str = Field(default_factory=_uuid)
    mitigation_type: MitigationType = Field(..., description="Category of mitigation action")
    priority: MitigationPriority = Field(..., description="Action priority")
    title: str = Field(..., description="Short action title")
    description: str = Field(..., description="Detailed action description")
    rationale: str = Field(default="", description="Why this action is recommended")
    knowledge_graph_refs: list[str] = Field(
        default_factory=list, description="Knowledge Graph node IDs relevant to this action"
    )
    graphrag_citations: list[str] = Field(
        default_factory=list, description="Document citations from GraphRAG retrieval"
    )
    root_cause_refs: list[str] = Field(
        default_factory=list, description="Root Cause Analysis finding IDs"
    )
    estimated_risk_reduction: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Estimated risk reduction (0.0-1.0)"
    )
    time_to_implement: str = Field(
        default="", description="Estimated implementation time (e.g. '2 hours')"
    )
    resources_required: list[str] = Field(
        default_factory=list, description="Required resources (personnel, equipment, etc.)"
    )
    applies_to: list[str] = Field(
        default_factory=list, description="Entity IDs this recommendation applies to"
    )
    generated_at: str = Field(default_factory=_now_iso)


class MitigationPlan(BaseModel):
    """Complete mitigation plan for a risk assessment.

    Aggregates multiple recommendations into a coordinated response plan
    with total expected risk reduction and implementation timeline.
    """

    model_config = ConfigDict(frozen=True)

    plan_id: str = Field(default_factory=_uuid)
    entity_id: str = Field(..., description="Target entity ID")
    entity_type: EntityType = Field(..., description="Target entity type")
    recommendations: list[RiskRecommendation] = Field(
        default_factory=list, description="Ordered list of mitigation recommendations"
    )
    total_estimated_risk_reduction: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Combined risk reduction if all actions taken"
    )
    approval_required: bool = Field(
        default=False, description="True if plan requires supervisor approval"
    )
    timeline: str = Field(default="", description="Overall implementation timeline")
    knowledge_graph_path: list[str] = Field(
        default_factory=list, description="Critical path nodes from Knowledge Graph"
    )
    evidence_sources: list[str] = Field(
        default_factory=list, description="Evidence sources used to generate plan"
    )
    generated_at: str = Field(default_factory=_now_iso)

    @property
    def immediate_actions(self) -> list[RiskRecommendation]:
        """Recommendations requiring immediate action."""
        return [
            r for r in self.recommendations if r.priority == MitigationPriority.IMMEDIATE
        ]

    @property
    def has_evacuation(self) -> bool:
        """True if plan includes evacuation recommendation."""
        return any(r.mitigation_type == MitigationType.EVACUATION for r in self.recommendations)


# ── Assessment Models ──────────────────────────────────────────────────────────


class RiskTimeline(BaseModel):
    """Historical risk trajectory for an entity."""

    model_config = ConfigDict(frozen=True)

    entity_id: str
    entity_type: EntityType
    entries: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of {timestamp, risk_value, risk_level, risk_type} entries",
    )
    window_minutes: int = Field(default=60)
    generated_at: str = Field(default_factory=_now_iso)


class RiskAssessment(BaseModel):
    """Complete risk assessment for any entity type.

    This is the primary output of the Predictive Risk Intelligence Platform.
    Combines current risk, multi-horizon forecasts, mitigation plan,
    trend analysis, and full explainability context.
    """

    model_config = ConfigDict(frozen=True)

    assessment_id: str = Field(default_factory=_uuid)
    entity_id: str = Field(..., description="Zone/Equipment/Worker/Plant ID")
    entity_type: EntityType = Field(..., description="Type of entity")
    timestamp: str = Field(default_factory=_now_iso)
    status: AssessmentStatus = Field(default=AssessmentStatus.COMPLETED)
    current_risk: RiskScore = Field(..., description="Current composite risk score")
    forecast: RiskForecast | None = Field(default=None, description="Multi-horizon forecast")
    mitigation_plan: MitigationPlan | None = Field(default=None)
    trend: RiskTrend | None = Field(default=None)
    top_factors: list[RiskFactor] = Field(
        default_factory=list, description="Top 10 contributing risk factors"
    )
    evidence: list[RiskEvidence] = Field(
        default_factory=list, description="Supporting evidence from all sources"
    )
    explanation: str = Field(default="", description="Human-readable assessment explanation")
    graphrag_citations: list[str] = Field(default_factory=list)
    root_cause_refs: list[str] = Field(default_factory=list)
    knowledge_graph_path: list[str] = Field(
        default_factory=list, description="Graph path to root hazard nodes"
    )
    latency_ms: float = Field(default=0.0, description="Total prediction pipeline latency")
    feature_vector_size: int = Field(default=0)
    risk_types_detected: list[RiskType] = Field(default_factory=list)


# ── Specialized Risk Assessment Types ─────────────────────────────────────────


class EquipmentRisk(BaseModel):
    """Equipment-specific risk assessment with maintenance context."""

    model_config = ConfigDict(frozen=True)

    assessment: RiskAssessment = Field(..., description="Base risk assessment")
    equipment_id: str = Field(..., description="Equipment Knowledge Graph node ID")
    equipment_type: str = Field(default="", description="Equipment classification")
    equipment_name: str = Field(default="", description="Human-readable equipment name")
    maintenance_overdue: bool = Field(default=False)
    days_since_maintenance: float | None = Field(default=None)
    last_maintenance_date: str | None = Field(default=None)
    failure_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    estimated_rul: float | None = Field(
        default=None, description="Remaining Useful Life in hours"
    )
    anomalous_sensor_ids: list[str] = Field(default_factory=list)
    connected_equipment_ids: list[str] = Field(default_factory=list)


class WorkerRisk(BaseModel):
    """Worker-specific risk assessment with exposure and PPE context."""

    model_config = ConfigDict(frozen=True)

    assessment: RiskAssessment = Field(..., description="Base risk assessment")
    worker_id: str = Field(..., description="Worker ID")
    worker_role: str = Field(default="", description="Worker role/designation")
    zone_id: str = Field(default="", description="Current zone")
    exposure_duration_hours: float = Field(
        default=0.0, ge=0.0, description="Hours exposed to current conditions"
    )
    ppe_compliance_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="PPE compliance from Vision Intelligence"
    )
    proximity_to_hazards: list[str] = Field(
        default_factory=list, description="Nearby hazard node IDs"
    )
    violation_count_24h: int = Field(default=0)


class ZoneRisk(BaseModel):
    """Zone-level aggregated risk assessment."""

    model_config = ConfigDict(frozen=True)

    assessment: RiskAssessment = Field(..., description="Base risk assessment")
    zone_id: str = Field(..., description="Zone identifier")
    zone_name: str = Field(default="")
    worker_count: int = Field(default=0, ge=0)
    equipment_ids: list[str] = Field(default_factory=list)
    active_equipment_risk_ids: list[str] = Field(default_factory=list)
    hazard_types: list[RiskType] = Field(default_factory=list)
    max_equipment_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_worker_ppe_compliance: float = Field(default=1.0, ge=0.0, le=1.0)


class PlantRisk(BaseModel):
    """Plant-wide composite risk assessment."""

    model_config = ConfigDict(frozen=True)

    assessment: RiskAssessment = Field(..., description="Base risk assessment")
    plant_id: str = Field(..., description="Plant identifier")
    plant_name: str = Field(default="")
    zone_count: int = Field(default=0, ge=0)
    active_hazard_count: int = Field(default=0, ge=0)
    overall_safety_index: float = Field(
        default=1.0, ge=0.0, le=1.0, description="1.0 = fully safe, 0.0 = maximum danger"
    )
    critical_zone_ids: list[str] = Field(default_factory=list)
    critical_equipment_ids: list[str] = Field(default_factory=list)
    environmental_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    operational_risk: float = Field(default=0.0, ge=0.0, le=1.0)


class CompositeRisk(BaseModel):
    """Composite risk score aggregating multiple risk dimensions for one entity."""

    model_config = ConfigDict(frozen=True)

    composite_id: str = Field(default_factory=_uuid)
    entity_id: str
    entity_type: EntityType
    equipment_risk: RiskScore | None = Field(default=None)
    worker_risk: RiskScore | None = Field(default=None)
    zone_risk: RiskScore | None = Field(default=None)
    environmental_risk: RiskScore | None = Field(default=None)
    operational_risk: RiskScore | None = Field(default=None)
    compliance_risk: RiskScore | None = Field(default=None)
    composite_score: RiskScore = Field(..., description="Weighted composite risk score")
    weights_used: dict[str, float] = Field(
        default_factory=dict, description="Dimension weights used in aggregation"
    )
    generated_at: str = Field(default_factory=_now_iso)


# ── Scenario Analysis ──────────────────────────────────────────────────────────


class RiskScenario(BaseModel):
    """What-if risk scenario with modified conditions.

    Allows simulation of risk under hypothetical conditions
    without affecting the live prediction pipeline.
    """

    model_config = ConfigDict(frozen=True)

    scenario_id: str = Field(default_factory=_uuid)
    name: str = Field(..., description="Scenario name")
    description: str = Field(default="", description="Scenario description")
    entity_id: str = Field(..., description="Target entity ID")
    entity_type: EntityType = Field(..., description="Target entity type")
    modified_conditions: dict[str, Any] = Field(
        default_factory=dict,
        description="Feature overrides for this scenario (feature_name → value)",
    )
    baseline_risk: RiskScore = Field(..., description="Risk under current conditions")
    scenario_risk: RiskScore = Field(..., description="Risk under scenario conditions")
    delta: float = Field(..., description="Risk change (scenario - baseline)")
    feasibility: float = Field(
        default=1.0, ge=0.0, le=1.0, description="How feasible this scenario is"
    )
    mitigation_scenario: bool = Field(
        default=False, description="True if this models a mitigation action"
    )
    created_at: str = Field(default_factory=_now_iso)
    created_by: str = Field(default="system")
