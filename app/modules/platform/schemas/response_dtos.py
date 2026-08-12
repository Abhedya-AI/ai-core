from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Any

class ModelVersionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    model_id: str
    name: str
    version: str
    stage: str
    status: str
    module: str
    model_family: str
    created_by: str
    created_at: str
    is_champion: bool
    metrics: dict[str, Any] | None = None
    tags: list[str] = []

class FeatureDefinitionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    feature_id: str
    name: str
    description: str
    feature_type: str
    entity_type: str
    source_module: str
    is_online: bool
    is_offline: bool
    ttl_seconds: int
    created_at: str
    version: int

class DriftReportResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    report_id: str
    model_id: str
    drift_type: str
    severity: str
    drift_score: float
    threshold: float
    is_alert: bool
    retraining_recommended: bool
    statistical_test: str
    detected_at: str

class TenantResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    tenant_id: str
    name: str
    slug: str
    tier: str
    is_active: bool
    contact_email: str
    created_at: str
    max_plants: int
    max_api_calls_per_minute: int

class OrganizationResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    org_id: str
    tenant_id: str
    name: str
    org_type: str
    parent_org_id: str | None
    plant_ids: list[str]
    member_ids: list[str]
    is_active: bool
    created_at: str

class PlantResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    plant_id: str
    tenant_id: str
    name: str
    location: str
    status: str
    plant_type: str
    oee_score: float | None
    safety_index: float | None
    equipment_count: int
    worker_count: int
    created_at: str

class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    key_id: str
    tenant_id: str
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool
    created_at: str
    expires_at: str | None
    raw_key: str | None = None

class HealthReportResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    overall_status: str
    components: dict[str, str]
    uptime_seconds: float
    active_alerts: list[str]
    generated_at: str

class GovernanceDecisionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    decision_id: str
    model_id: str
    entity_id: str
    decision_type: str
    confidence: float
    all_policies_passed: bool
    requires_review: bool
    decided_at: str

class ComplianceReportResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    report_id: str
    model_id: str
    model_version: str
    reporting_period: str
    total_predictions: int
    policy_violations: int
    fairness_score: float
    responsible_ai_score: float
    is_compliant: bool
    generated_at: str
    recommendations: list[str]

class PlatformAnalyticsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    active_tenants: int
    total_model_versions: int
    total_features: int
    drift_alerts_last_24h: int
    retraining_jobs_completed: int
    api_calls_last_hour: int
    generated_at: str

class CostSummaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    tenant_id: str
    period: str
    total_cost_usd: float
    api_cost_usd: float
    compute_cost_usd: float
    storage_cost_usd: float
    simulation_cost_usd: float
    generated_at: str

class LicenseResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    tenant_id: str
    tier: str
    valid: bool
    expired: bool
    days_remaining: int | None
    features: list[str]
    issued_at: str
    expires_at: str | None
