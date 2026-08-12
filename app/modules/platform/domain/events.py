from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from .enums import (
    DriftType, DriftSeverity, RetrainingTrigger, HealthStatus,
    GovernancePolicy, ModelStage, DeploymentStrategy, TenantTier
)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uuid() -> str:
    return str(uuid.uuid4())

class PlatformDomainEvent(BaseModel):
    """Base class for all Platform domain events."""
    model_config = ConfigDict(frozen=True)
    event_id: str = Field(default_factory=_uuid)
    occurred_at: str = Field(default_factory=_now_iso)
    tenant_id: str = ""
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

class ModelRegistered(PlatformDomainEvent):
    model_id: str
    name: str
    version_str: str
    module: str
    created_by: str

class ModelPromoted(PlatformDomainEvent):
    model_id: str
    name: str
    from_stage: ModelStage
    to_stage: ModelStage
    approved_by: str
    strategy: DeploymentStrategy | None = None

class ModelRejected(PlatformDomainEvent):
    model_id: str
    name: str
    version_str: str
    rejected_by: str
    reason: str

class FeatureUpdated(PlatformDomainEvent):
    feature_id: str
    name: str
    entity_type: str
    source_module: str
    version_num: int

class DriftDetected(PlatformDomainEvent):
    model_id: str
    drift_type: DriftType
    severity: DriftSeverity
    drift_score: float
    threshold: float
    retraining_recommended: bool

class RetrainingStarted(PlatformDomainEvent):
    job_id: str
    model_id: str
    trigger: RetrainingTrigger
    feedback_count: int

class RetrainingCompleted(PlatformDomainEvent):
    job_id: str
    model_id: str
    trigger: RetrainingTrigger
    improvement_delta: float | None
    new_version: str

class GovernanceAlert(PlatformDomainEvent):
    model_id: str
    policy: GovernancePolicy
    violation_type: str
    entity_id: str
    confidence: float

class PlatformHealthChanged(PlatformDomainEvent):
    from_status: HealthStatus
    to_status: HealthStatus
    affected_components: list[str]
    active_alerts: int

class DeploymentCompleted(PlatformDomainEvent):
    deployment_id: str
    model_id: str
    strategy: DeploymentStrategy
    environment: str
    traffic_pct: float
    replicas: int

class TenantCreated(PlatformDomainEvent):
    tenant_id: str
    name: str
    tier: TenantTier
    max_plants: int

class QuotaExceeded(PlatformDomainEvent):
    tenant_id: str
    quota_type: str
    used: float
    limit: float

PLATFORM_EVENT_TOPICS: dict[str, str] = {
    "ModelRegistered": "platform.model.registered",
    "ModelPromoted": "platform.model.promoted",
    "ModelRejected": "platform.model.rejected",
    "FeatureUpdated": "platform.feature.updated",
    "DriftDetected": "platform.drift.detected",
    "RetrainingStarted": "platform.retraining.started",
    "RetrainingCompleted": "platform.retraining.completed",
    "GovernanceAlert": "platform.governance.alert",
    "PlatformHealthChanged": "platform.health.changed",
    "DeploymentCompleted": "platform.deployment.completed",
    "TenantCreated": "platform.tenant.created",
    "QuotaExceeded": "platform.quota.exceeded",
}
