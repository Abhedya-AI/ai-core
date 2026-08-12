from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Optional

class RegisterModelRequest(BaseModel):
    name: str
    description: str = ""
    version: str = "1.0.0"  # semver
    module: str  # which AI module this model belongs to
    model_family: str = "HYBRID"
    feature_names: list[str] = []
    hyperparameters: dict[str, Any] = {}
    tags: list[str] = []
    created_by: str
    training_data_hash: str = ""
    deployment_config: dict[str, Any] = {}

class PromoteModelRequest(BaseModel):
    to_stage: str  # ModelStage value
    approved_by: str
    justification: str = ""

class SubmitForReviewRequest(BaseModel):
    submitted_by: str
    justification: str

class ApproveModelRequest(BaseModel):
    approver_id: str
    comments: str = ""

class RejectModelRequest(BaseModel):
    rejector_id: str
    reason: str

class CreateFeatureRequest(BaseModel):
    name: str
    description: str = ""
    owner: str
    feature_type: str  # FeatureType value
    entity_type: str
    source_module: str
    tags: list[str] = []
    is_online: bool = True
    is_offline: bool = True
    ttl_seconds: int = 300
    validation_rules: dict[str, Any] = {}
    lineage_sources: list[str] = []

class ServeFeatureRequest(BaseModel):
    entity_id: str
    feature_group: str
    entity_type: str

class MaterializeFeatureRequest(BaseModel):
    entity_id: str
    entity_type: str
    features: dict[str, Any]
    source_module: str
    timestamp: str | None = None

class RunDriftCheckRequest(BaseModel):
    model_id: str
    baseline_data: list[float] = []
    current_data: list[float] = []
    feature_name: str = "default"
    baseline_predictions: list[float] = []
    current_predictions: list[float] = []
    recent_errors: list[float] = []
    recent_metrics: dict[str, float] = {}

class SubmitFeedbackRequest(BaseModel):
    model_id: str
    entity_id: str
    entity_type: str
    prediction: float
    actual: float | None = None
    confidence: float
    feedback_source: str = "human"
    feedback_type: str = "risk"  # "risk", "forecast", "hazard", "rca", "twin", "simulation"
    metadata: dict[str, Any] = {}

class CreateTenantRequest(BaseModel):
    name: str
    slug: str
    description: str = ""
    tier: str = "COMMUNITY"  # TenantTier value
    contact_email: str

class CreateOrganizationRequest(BaseModel):
    tenant_id: str
    name: str
    description: str = ""
    org_type: str = "DIVISION"
    parent_org_id: str | None = None
    plant_ids: list[str] = []
    member_ids: list[str] = []

class RegisterPlantRequest(BaseModel):
    tenant_id: str
    name: str
    location: str
    description: str = ""
    plant_type: str
    timezone: str = "UTC"
    metadata: dict[str, Any] = {}

class CreateApiKeyRequest(BaseModel):
    name: str
    description: str = ""
    scopes: list[str] = ["READ"]
    created_by: str
    expires_at: str | None = None

class GenerateReportRequest(BaseModel):
    model_id: str
    model_version: str
    reporting_period: str  # "YYYY-MM"
    tenant_id: str

class UpdatePlantMetricsRequest(BaseModel):
    oee_score: float | None = None
    safety_index: float | None = None
    equipment_count: int | None = None
    worker_count: int | None = None

class ABACPolicyRequest(BaseModel):
    name: str
    description: str = ""
    effect: str = "ALLOW"  # "ALLOW" or "DENY"
    subjects: list[str] = []
    resources: list[str] = []
    actions: list[str] = []
    conditions: dict[str, Any] = {}
    priority: int = 100

class IssueLicenseRequest(BaseModel):
    tenant_id: str
    tier: str  # LicenseTier
    expires_at: str | None = None
