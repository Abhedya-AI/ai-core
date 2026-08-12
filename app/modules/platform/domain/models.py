from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, computed_field

from .enums import (
    ModelStage, ModelStatus, ApprovalStatus, DriftType, DriftSeverity,
    FeatureType, TenantTier, PlantStatus, GovernancePolicy, DeploymentStrategy,
    AlertSeverity, HealthStatus, LicenseTier, AuditAction, RetrainingTrigger,
    OnlineLearningStatus
)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uuid() -> str:
    return str(uuid.uuid4())

class ModelMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    auc_roc: float | None = None
    mae: float | None = None
    rmse: float | None = None
    mape: float | None = None
    inference_latency_ms: float
    throughput_rps: float
    memory_mb: float
    evaluated_at: str = Field(default_factory=_now_iso)
    dataset_size: int

    @computed_field
    @property
    def is_production_ready(self) -> bool:
        return bool(
            self.f1_score is not None and self.f1_score > 0.7 
            and self.inference_latency_ms < 500
        )

class ModelVersion(BaseModel):
    model_config = ConfigDict(frozen=True)
    model_id: str = Field(default_factory=_uuid)
    name: str
    description: str
    version: str
    stage: ModelStage
    status: ModelStatus
    module: str
    model_family: str
    metrics: ModelMetrics | None = None
    training_data_hash: str
    feature_names: list[str]
    hyperparameters: dict[str, Any]
    tags: list[str]
    created_by: str
    approved_by: str | None = None
    created_at: str = Field(default_factory=_now_iso)
    approved_at: str | None = None
    deployment_config: dict[str, Any]
    lineage_parent_ids: list[str]

    @computed_field
    @property
    def is_champion(self) -> bool:
        return self.stage == ModelStage.PRODUCTION

    @computed_field
    @property
    def major_version(self) -> int:
        try:
            return int(self.version.split(".")[0])
        except (ValueError, IndexError):
            return 0
            
    @computed_field
    @property
    def minor_version(self) -> int:
        try:
            return int(self.version.split(".")[1])
        except (ValueError, IndexError):
            return 0
            
    @computed_field
    @property
    def patch_version(self) -> int:
        try:
            return int(self.version.split(".")[2])
        except (ValueError, IndexError):
            return 0

class ModelLineage(BaseModel):
    model_config = ConfigDict(frozen=True)
    lineage_id: str = Field(default_factory=_uuid)
    model_id: str
    parent_model_ids: list[str]
    training_datasets: list[str]
    feature_names: list[str]
    transformations: list[str]
    created_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def depth(self) -> int:
        return len(self.parent_model_ids)

class FeatureDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)
    feature_id: str = Field(default_factory=_uuid)
    name: str
    description: str
    owner: str
    feature_type: FeatureType
    entity_type: str
    source_module: str
    tags: list[str]
    is_online: bool
    is_offline: bool
    ttl_seconds: int
    created_at: str = Field(default_factory=_now_iso)
    version: int = 1
    lineage_sources: list[str]
    validation_rules: dict[str, Any]

class FeatureVector(BaseModel):
    model_config = ConfigDict(frozen=True)
    vector_id: str = Field(default_factory=_uuid)
    entity_id: str
    entity_type: str
    feature_values: dict[str, float | str | bool]
    timestamp: str = Field(default_factory=_now_iso)
    source_module: str
    ttl_seconds: int = 300

class DriftReport(BaseModel):
    model_config = ConfigDict(frozen=True)
    report_id: str = Field(default_factory=_uuid)
    model_id: str
    drift_type: DriftType
    severity: DriftSeverity
    drift_score: float
    threshold: float = 0.2
    feature_scores: dict[str, float]
    statistical_test: str
    test_statistic: float
    p_value: float | None = None
    is_alert: bool
    retraining_recommended: bool
    detected_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def is_critical(self) -> bool:
        return self.severity == DriftSeverity.CRITICAL

    @computed_field
    @property
    def action_required(self) -> bool:
        return self.is_alert and self.retraining_recommended

class TenantProfile(BaseModel):
    model_config = ConfigDict(frozen=True)
    tenant_id: str = Field(default_factory=_uuid)
    name: str
    slug: str
    description: str
    tier: TenantTier
    is_active: bool = True
    created_at: str = Field(default_factory=_now_iso)
    contact_email: str
    max_plants: int
    max_api_calls_per_minute: int
    max_model_versions: int
    max_storage_gb: float

    @computed_field
    @property
    def is_enterprise(self) -> bool:
        return self.tier in [TenantTier.ENTERPRISE, TenantTier.GOVERNMENT]

class PlantProfile(BaseModel):
    model_config = ConfigDict(frozen=True)
    plant_id: str = Field(default_factory=_uuid)
    tenant_id: str
    name: str
    location: str
    description: str
    status: PlantStatus
    plant_type: str
    timezone: str = "UTC"
    created_at: str = Field(default_factory=_now_iso)
    metadata: dict[str, Any]
    equipment_count: int = 0
    worker_count: int = 0
    zone_count: int = 0
    oee_score: float | None = None
    safety_index: float | None = None

    @computed_field
    @property
    def is_operational(self) -> bool:
        return self.status == PlantStatus.ACTIVE

class OrganizationProfile(BaseModel):
    model_config = ConfigDict(frozen=True)
    org_id: str = Field(default_factory=_uuid)
    tenant_id: str
    name: str
    description: str
    org_type: str
    parent_org_id: str | None = None
    plant_ids: list[str]
    member_ids: list[str]
    created_at: str = Field(default_factory=_now_iso)
    is_active: bool = True

class GovernanceDecision(BaseModel):
    model_config = ConfigDict(frozen=True)
    decision_id: str = Field(default_factory=_uuid)
    model_id: str
    entity_id: str
    entity_type: str
    model_name: str
    model_version: str
    decision_type: str
    input_features: dict[str, Any]
    output: dict[str, Any]
    confidence: float
    explanation: dict[str, Any]
    policy_checks: list[dict[str, Any]]
    all_policies_passed: bool
    decided_at: str = Field(default_factory=_now_iso)
    tenant_id: str
    plant_id: str | None = None

    @computed_field
    @property
    def requires_review(self) -> bool:
        return not self.all_policies_passed or self.confidence < 0.5

class ComplianceReport(BaseModel):
    model_config = ConfigDict(frozen=True)
    report_id: str = Field(default_factory=_uuid)
    model_id: str
    model_name: str
    model_version: str
    reporting_period: str
    total_predictions: int
    policy_violations: int
    fairness_score: float
    bias_metrics: dict[str, float]
    confidence_calibration_error: float
    data_lineage_complete: bool
    responsible_ai_score: float
    generated_at: str = Field(default_factory=_now_iso)
    recommendations: list[str]

    @computed_field
    @property
    def is_compliant(self) -> bool:
        return self.policy_violations == 0 and self.responsible_ai_score > 0.7

class DeploymentRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    deployment_id: str = Field(default_factory=_uuid)
    model_id: str
    model_version: str
    strategy: DeploymentStrategy
    target_environment: str
    deployed_by: str
    deployed_at: str = Field(default_factory=_now_iso)
    is_active: bool = True
    rollback_model_id: str | None = None
    health_check_url: str | None = None
    traffic_percentage: float = 100.0
    replicas: int = 3
    config: dict[str, Any]

class HealthReport(BaseModel):
    model_config = ConfigDict(frozen=True)
    report_id: str = Field(default_factory=_uuid)
    overall_status: HealthStatus
    components: dict[str, HealthStatus]
    component_latencies_ms: dict[str, float]
    active_alerts: list[str]
    uptime_seconds: float
    generated_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def is_healthy(self) -> bool:
        return self.overall_status == HealthStatus.HEALTHY

    @computed_field
    @property
    def degraded_components(self) -> list[str]:
        return [c for c, status in self.components.items() if status != HealthStatus.HEALTHY]

class CostRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    record_id: str = Field(default_factory=_uuid)
    tenant_id: str
    period: str
    api_calls: int
    api_cost_usd: float
    compute_units: float
    compute_cost_usd: float
    storage_gb: float
    storage_cost_usd: float
    simulation_units: int
    simulation_cost_usd: float
    total_cost_usd: float
    created_at: str = Field(default_factory=_now_iso)

class QuotaUsage(BaseModel):
    model_config = ConfigDict(frozen=True)
    tenant_id: str
    api_calls_this_minute: int
    api_calls_limit: int
    model_versions_count: int
    model_versions_limit: int
    storage_gb_used: float
    storage_gb_limit: float
    active_simulations: int
    active_simulations_limit: int
    checked_at: str = Field(default_factory=_now_iso)

    @computed_field
    @property
    def api_calls_pct(self) -> float:
        return self.api_calls_this_minute / self.api_calls_limit if self.api_calls_limit else 0.0

    @computed_field
    @property
    def storage_pct(self) -> float:
        return self.storage_gb_used / self.storage_gb_limit if self.storage_gb_limit else 0.0

    @computed_field
    @property
    def is_over_limit(self) -> bool:
        return (
            self.api_calls_this_minute > self.api_calls_limit or
            self.model_versions_count > self.model_versions_limit or
            self.storage_gb_used > self.storage_gb_limit or
            self.active_simulations > self.active_simulations_limit
        )

class ApiKey(BaseModel):
    model_config = ConfigDict(frozen=True)
    key_id: str = Field(default_factory=_uuid)
    tenant_id: str
    name: str
    description: str
    key_hash: str
    key_prefix: str
    scopes: list[str]
    is_active: bool = True
    created_at: str = Field(default_factory=_now_iso)
    expires_at: str | None = None
    last_used_at: str | None = None
    created_by: str

    @computed_field
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return self.expires_at < _now_iso()

class RBACRole(BaseModel):
    model_config = ConfigDict(frozen=True)
    role_id: str = Field(default_factory=_uuid)
    name: str
    description: str
    permissions: list[str]
    parent_role: str | None = None
    is_system_role: bool = False
    created_at: str = Field(default_factory=_now_iso)

class ABACPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)
    policy_id: str = Field(default_factory=_uuid)
    name: str
    description: str
    effect: str
    subjects: list[str]
    resources: list[str]
    actions: list[str]
    conditions: dict[str, Any]
    priority: int
    is_active: bool = True
    created_at: str = Field(default_factory=_now_iso)

class AuditExtension(BaseModel):
    model_config = ConfigDict(frozen=True)
    audit_id: str = Field(default_factory=_uuid)
    action: AuditAction
    actor_id: str
    actor_type: str
    resource_id: str
    resource_type: str
    tenant_id: str
    details: dict[str, Any]
    ip_address: str | None = None
    user_agent: str | None = None
    occurred_at: str = Field(default_factory=_now_iso)
    is_sensitive: bool = False
    pii_encrypted: bool = False

class OnlineLearningJob(BaseModel):
    model_config = ConfigDict(frozen=True)
    job_id: str = Field(default_factory=_uuid)
    model_id: str
    trigger: RetrainingTrigger
    status: OnlineLearningStatus
    feedback_count: int
    improvement_delta: float | None = None
    started_at: str = Field(default_factory=_now_iso)
    completed_at: str | None = None
    error_message: str | None = None

    @computed_field
    @property
    def duration_seconds(self) -> float | None:
        if not self.completed_at:
            return None
        t1 = datetime.fromisoformat(self.started_at)
        t2 = datetime.fromisoformat(self.completed_at)
        return (t2 - t1).total_seconds()
