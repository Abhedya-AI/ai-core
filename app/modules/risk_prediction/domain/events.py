"""
app/modules/risk_prediction/domain/events.py — Risk Prediction domain events.

Typed domain events published to the Event Platform (Kafka) when
significant risk prediction milestones occur.

All events are immutable Pydantic v2 models with UTC timestamps.
Published via the existing EventBus infrastructure.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.risk_prediction.domain.enums import (
    EntityType,
    RiskLevel,
    RiskType,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


class RiskDomainEvent(BaseModel):
    """Base class for all Risk Prediction domain events."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=_uuid)
    event_type: str = Field(..., description="Discriminator field")
    timestamp: str = Field(default_factory=_now_iso)
    source: str = Field(default="risk_prediction", description="Source module")
    correlation_id: str | None = Field(
        default=None, description="Links related events"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskCalculated(RiskDomainEvent):
    """Emitted when a risk assessment is successfully computed.

    Triggers downstream consumers: Dashboard, Notifications, Supervisor.
    Topic: risk.calculated
    """

    event_type: str = Field(default="RiskCalculated")
    entity_id: str = Field(..., description="Entity that was assessed")
    entity_type: EntityType = Field(...)
    assessment_id: str = Field(..., description="Risk assessment identifier")
    risk_value: float = Field(..., ge=0.0, le=1.0, description="Computed risk score")
    risk_level: RiskLevel = Field(..., description="Categorical risk level")
    confidence: float = Field(..., ge=0.0, le=1.0)
    dominant_risk_type: RiskType | None = Field(default=None)
    latency_ms: float = Field(default=0.0)


class RiskForecastGenerated(RiskDomainEvent):
    """Emitted when a multi-horizon risk forecast is generated.

    Topic: risk.forecast.generated
    """

    event_type: str = Field(default="RiskForecastGenerated")
    forecast_id: str = Field(...)
    entity_id: str = Field(...)
    entity_type: EntityType = Field(...)
    horizons: list[str] = Field(
        ..., description="List of forecast horizons generated (e.g. ['5m','1h','24h'])"
    )
    peak_risk_value: float = Field(default=0.0, ge=0.0, le=1.0)
    peak_horizon: str = Field(default="")
    generated_at: str = Field(default_factory=_now_iso)


class RiskThresholdExceeded(RiskDomainEvent):
    """Emitted when risk crosses a configured alert threshold.

    Triggers Notification Framework and Supervisor escalation.
    Topic: risk.threshold.exceeded
    """

    event_type: str = Field(default="RiskThresholdExceeded")
    entity_id: str = Field(...)
    entity_type: EntityType = Field(...)
    risk_type: RiskType = Field(...)
    threshold_value: float = Field(..., ge=0.0, le=1.0)
    actual_value: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel = Field(...)
    previous_level: RiskLevel | None = Field(default=None)
    assessment_id: str = Field(default="")


class MitigationGenerated(RiskDomainEvent):
    """Emitted when a mitigation plan is generated for an entity.

    Topic: risk.mitigation.generated
    """

    event_type: str = Field(default="MitigationGenerated")
    plan_id: str = Field(...)
    entity_id: str = Field(...)
    entity_type: EntityType = Field(...)
    recommendation_count: int = Field(..., ge=0)
    estimated_risk_reduction: float = Field(default=0.0, ge=0.0, le=1.0)
    has_immediate_actions: bool = Field(default=False)
    has_evacuation: bool = Field(default=False)
    assessment_id: str = Field(default="")


class RiskEscalated(RiskDomainEvent):
    """Emitted when risk level escalates (e.g. MEDIUM → HIGH).

    Triggers immediate Supervisor notification and potential emergency response.
    Topic: risk.escalated
    """

    event_type: str = Field(default="RiskEscalated")
    entity_id: str = Field(...)
    entity_type: EntityType = Field(...)
    from_level: RiskLevel = Field(...)
    to_level: RiskLevel = Field(...)
    risk_type: RiskType = Field(...)
    risk_value: float = Field(..., ge=0.0, le=1.0)
    assessment_id: str = Field(default="")
    escalation_velocity: float = Field(
        default=0.0, description="Rate of risk increase (per minute)"
    )


class PredictionCompleted(RiskDomainEvent):
    """Emitted upon successful prediction pipeline completion.

    Used for observability and SLA tracking.
    Topic: risk.prediction.completed
    """

    event_type: str = Field(default="PredictionCompleted")
    prediction_id: str = Field(...)
    entity_id: str = Field(...)
    entity_type: EntityType = Field(...)
    latency_ms: float = Field(..., ge=0.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    feature_count: int = Field(default=0)
    model_type: str = Field(default="ENSEMBLE")
    horizons_generated: int = Field(default=0)


# Topic names for Kafka routing
RISK_EVENT_TOPICS = {
    "RiskCalculated": "risk.calculated",
    "RiskForecastGenerated": "risk.forecast.generated",
    "RiskThresholdExceeded": "risk.threshold.exceeded",
    "MitigationGenerated": "risk.mitigation.generated",
    "RiskEscalated": "risk.escalated",
    "PredictionCompleted": "risk.prediction.completed",
}
