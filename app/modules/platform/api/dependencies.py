from __future__ import annotations
from typing import Annotated
from fastapi import Depends
from app.core.logging import get_logger
log = get_logger(__name__)

try:
    from app.modules.platform.services.platform_orchestration_service import PlatformOrchestrationService
except ImportError:
    class PlatformOrchestrationService:
        def __init__(self, **kwargs): pass
        async def list_models(self, module, stage, limit, offset): return []
        async def register_model(self, request, tenant_id): return {}
        async def get_model(self, model_id): return {}
        async def promote_model(self, model_id, request): return {}
        async def approve_model_workflow(self, model_id, request): return {}
        async def approve_model(self, model_id, request): return {}
        async def reject_model(self, model_id, request): return {}
        async def get_model_lineage(self, model_id): return {}
        async def get_model_metrics(self, model_id): return {}
        async def compare_models(self, model_id_a, model_id_b): return {}
        async def list_features(self, entity_type, source_module, limit, offset): return []
        async def register_feature(self, request): return {}
        async def get_feature(self, feature_id): return {}
        async def serve_feature(self, request): return {}
        async def materialize_feature(self, request): return {}
        async def validate_feature(self, feature_id, value): return {}
        async def get_feature_statistics(self, feature_id, entity_id): return {}
        async def get_feature_lineage(self, feature_id): return {}
        async def get_drift_status(self, model_id): return {}
        async def run_drift_check(self, request): return {}
        async def get_drift_history(self, model_id, limit): return []
        async def get_feature_drift(self, model_id, feature_name): return {}
        async def get_performance_metrics(self, module, window_minutes): return {}
        async def get_ai_pipeline_metrics(self, module, window_minutes): return {}
        async def get_retraining_jobs(self, model_id, limit): return []
        async def submit_feedback(self, request): return {}
        async def list_governance_decisions(self, model_id, limit, offset): return []
        async def get_governance_decision(self, decision_id): return {}
        async def list_pending_approvals(self, tenant_id): return []
        async def list_policies(self): return []
        async def add_policy(self, name, policy_type, rule, threshold): return {}
        async def get_compliance_report(self, model_id, model_version, reporting_period, tenant_id): return {}
        async def get_explainability(self, model_id, prediction_id): return {}
        async def get_governance_audit(self, tenant_id, action, limit): return []
        async def create_api_key(self, request, tenant_id): return {}
        async def list_api_keys(self, tenant_id): return []
        async def revoke_api_key(self, key_id, revoked_by): return {}
        async def list_rbac_roles(self): return []
        async def get_role_permissions(self, role): return []
        async def add_abac_policy(self, request): return {}
        async def list_abac_policies(self): return []
        async def get_rate_limit_status(self, tenant_id): return {}
        async def list_organizations(self, tenant_id, limit, offset): return []
        async def create_organization(self, request): return {}
        async def get_organization(self, org_id): return {}
        async def update_organization(self, org_id, updates): return {}
        async def list_members(self, org_id): return []
        async def add_member(self, org_id, user_id): return {}
        async def list_plants(self, tenant_id, status, limit, offset): return []
        async def register_plant(self, request): return {}
        async def get_plant(self, plant_id): return {}
        async def get_fleet_health(self, tenant_id): return {}
        async def get_fleet_analytics(self, tenant_id): return {}
        async def get_fleet_benchmarks(self, tenant_id): return {}
        async def update_plant_metrics(self, plant_id, request): return {}
        async def deregister_plant(self, plant_id): return {}
        async def get_system_status(self): return {}
        async def enable_maintenance(self, reason, enabled_by): return {}
        async def disable_maintenance(self, disabled_by): return {}
        async def get_system_config(self): return {}
        async def list_all_tenants(self, tier, is_active, limit, offset): return []
        async def create_tenant(self, request): return {}
        async def suspend_tenant(self, tenant_id, reason, by): return {}
        async def get_cost_summary(self, tenant_id, period): return {}
        async def get_platform_analytics(self): return {}
        async def get_model_analytics(self, module, days): return {}
        async def get_feature_analytics(self): return {}
        async def get_tenant_analytics(self, tenant_id): return {}
        async def get_executive_summary(self): return {}
        async def export_analytics(self, format, tenant_id): return {}
        async def get_platform_health(self): return {}
        async def get_component_health(self, component): return {}
        async def readiness_check(self): return {}
        async def liveness_check(self): return {}

_platform_service_instance: PlatformOrchestrationService | None = None

def _get_or_create_platform_service() -> PlatformOrchestrationService:
    global _platform_service_instance
    if _platform_service_instance is None:
        try:
            from app.modules.platform.model_registry.registry import ModelRegistry
            from app.modules.platform.feature_store.feature_registry import FeatureRegistry
            from app.modules.platform.drift_detection.drift_orchestrator import DriftOrchestrator
            from app.modules.platform.governance.decision_logger import AIDecisionLogger
            from app.modules.platform.governance.approval_workflow import ModelApprovalWorkflow
            from app.modules.platform.governance.responsible_ai import ResponsibleAIReporter
            from app.modules.platform.multitenancy.tenant_manager import TenantManager
            from app.modules.platform.organizations.org_service import OrganizationService
            from app.modules.platform.plants.plant_registry import PlantRegistry
            from app.modules.platform.plants.fleet_health import FleetHealthMonitor
            from app.modules.platform.security.rbac import RBACManager
            from app.modules.platform.security.api_key_manager import APIKeyManager
            from app.modules.platform.licensing.license_manager import LicenseManager
            _platform_service_instance = PlatformOrchestrationService(
                model_registry=ModelRegistry(),
                feature_registry=FeatureRegistry(),
                drift_orchestrator=DriftOrchestrator(),
                decision_logger=AIDecisionLogger(),
                approval_workflow=ModelApprovalWorkflow(),
                responsible_ai=ResponsibleAIReporter(),
                tenant_manager=TenantManager(),
                organization_service=OrganizationService(),
                plant_registry=PlantRegistry(),
                fleet_health=FleetHealthMonitor(),
                rbac_manager=RBACManager(),
                api_key_manager=APIKeyManager(),
                license_manager=LicenseManager()
            )
        except Exception as e:
            log.warning(f"Platform service partial init: {e}")
            _platform_service_instance = PlatformOrchestrationService()
    return _platform_service_instance

def get_platform_service() -> PlatformOrchestrationService:
    return _get_or_create_platform_service()

PlatformServiceDep = Annotated[PlatformOrchestrationService, Depends(get_platform_service)]
