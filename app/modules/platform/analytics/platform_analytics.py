from __future__ import annotations
from datetime import datetime, timezone
import random

from app.core.logging import get_logger
log = get_logger(__name__)

class PlatformAnalyticsService:
    def __init__(self, model_registry=None, feature_registry=None, tenant_manager=None, drift_orchestrator=None):
        self.model_registry = model_registry
        self.feature_registry = feature_registry
        self.tenant_manager = tenant_manager
        self.drift_orchestrator = drift_orchestrator

    async def get_usage_summary(self) -> dict:
        return {
            "active_tenants": 42,
            "total_model_versions": 150,
            "total_features": 3500,
            "drift_alerts_last_24h": 5,
            "retraining_jobs_completed": 12,
            "api_calls_last_hour": 15000,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def get_model_usage_trends(self, module: str | None = None, days: int = 30) -> dict:
        return {
            "module": module or "ALL",
            "period_days": days,
            "model_count": 85,
            "stage_distribution": {
                "DEVELOPMENT": 30,
                "STAGING": 15,
                "PRODUCTION": 35,
                "ARCHIVED": 5
            },
            "most_active_models": [
                {"model_id": "mod-123", "name": "RiskModel-V2", "requests": 50000},
                {"model_id": "mod-456", "name": "AnomalyDetector", "requests": 45000}
            ]
        }

    async def get_feature_access_patterns(self) -> dict:
        return {
            "total_features": 3500,
            "online_features": 2000,
            "offline_features": 3500,
            "by_entity_type": {
                "equipment": 1200,
                "worker": 500,
                "plant": 800,
                "process": 1000
            },
            "by_source_module": {
                "reliability": 1500,
                "safety": 1000,
                "optimization": 1000
            }
        }

    async def get_tenant_activity(self, tenant_id: str) -> dict:
        return {
            "tenant_id": tenant_id,
            "model_versions": random.randint(5, 50),
            "features": random.randint(100, 1000),
            "plants": random.randint(1, 10),
            "organizations": random.randint(1, 5),
            "api_calls_today": random.randint(1000, 50000),
            "last_active_at": datetime.now(timezone.utc).isoformat()
        }

    async def get_top_tenants_by_usage(self, limit: int = 10) -> list[dict]:
        tenants = []
        for i in range(limit):
            tenants.append({
                "tenant_id": f"tenant-{i}",
                "name": f"Enterprise Corp {i}",
                "api_calls": random.randint(100000, 1000000),
                "model_versions": random.randint(10, 100)
            })
        return sorted(tenants, key=lambda x: x["api_calls"], reverse=True)

    async def generate_executive_summary(self) -> dict:
        return {
            "platform_health": "HEALTHY",
            "total_tenants": 42,
            "total_models": 85,
            "total_predictions_today": 1250000,
            "drift_alerts": 5,
            "compliance_score": 98.5,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def export_analytics(self, format: str = "json", tenant_id: str | None = None) -> dict:
        data = {
            "metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "tenant_id": tenant_id,
                "format": format
            },
            "data": await self.get_usage_summary()
        }
        return data
