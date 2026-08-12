from __future__ import annotations
try:
    from app.modules.platform.schemas.request_dtos import (
        RegisterModelRequest, PromoteModelRequest, SubmitForReviewRequest,
        ApproveModelRequest, RejectModelRequest, CreateFeatureRequest,
        ServeFeatureRequest, MaterializeFeatureRequest, RunDriftCheckRequest,
        SubmitFeedbackRequest, CreateTenantRequest, CreateOrganizationRequest,
        RegisterPlantRequest, CreateApiKeyRequest, GenerateReportRequest,
        UpdatePlantMetricsRequest, ABACPolicyRequest, IssueLicenseRequest,
    )
    from app.modules.platform.schemas.response_dtos import (
        ModelVersionResponse, FeatureDefinitionResponse, DriftReportResponse,
        TenantResponse, OrganizationResponse, PlantResponse, ApiKeyResponse,
        HealthReportResponse, GovernanceDecisionResponse, ComplianceReportResponse,
        PlatformAnalyticsResponse, CostSummaryResponse, LicenseResponse,
    )
except ImportError:
    pass
