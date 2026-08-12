from __future__ import annotations
import time
from typing import Any
from datetime import datetime, timezone
import uuid

from app.core.logging import get_logger
log = get_logger(__name__)

try:
    from app.infrastructure.kafka.producer import EventBus
except ImportError:
    EventBus = None

try:
    from app.modules.platform.domain.events import (
        PlatformDomainEvent, ModelRegistered, ModelPromoted, ModelRejected,
        FeatureUpdated, DriftDetected, RetrainingStarted, RetrainingCompleted,
        GovernanceAlert, PlatformHealthChanged, DeploymentCompleted,
        TenantCreated, QuotaExceeded, PLATFORM_EVENT_TOPICS
    )
except ImportError:
    class PlatformDomainEvent: pass
    class ModelRegistered: pass
    class ModelPromoted: pass
    class ModelRejected: pass
    class FeatureUpdated: pass
    class DriftDetected: pass
    class RetrainingStarted: pass
    class RetrainingCompleted: pass
    class GovernanceAlert: pass
    class PlatformHealthChanged: pass
    class DeploymentCompleted: pass
    class TenantCreated: pass
    class QuotaExceeded: pass
    PLATFORM_EVENT_TOPICS = {
        "ModelRegistered": "platform.model.registered",
        "ModelPromoted": "platform.model.promoted",
        "ModelRejected": "platform.model.rejected",
        "FeatureUpdated": "platform.feature.updated",
        "DriftDetected": "platform.model.drift_detected",
        "RetrainingStarted": "platform.model.retraining_started",
        "RetrainingCompleted": "platform.model.retraining_completed",
        "GovernanceAlert": "platform.governance.alert",
        "PlatformHealthChanged": "platform.health.changed",
        "DeploymentCompleted": "platform.model.deployment_completed",
        "TenantCreated": "platform.tenant.created",
        "QuotaExceeded": "platform.tenant.quota_exceeded"
    }

class PlatformEventPublisher:
    def __init__(self, event_bus: Any | None = None):
        self.event_bus = event_bus

    async def _publish(self, event: Any, event_type: str) -> None:
        topic = PLATFORM_EVENT_TOPICS.get(event_type, "platform.events")
        event_dict = event.__dict__ if hasattr(event, "__dict__") else {}
        log.info(f"Publishing event {event_type} to topic {topic}: {event_dict}")
        
        if self.event_bus:
            try:
                await self.event_bus.publish(topic, event_dict)
            except Exception as e:
                log.error(f"Failed to publish event {event_type}: {e}")

    def _create_base_event(self) -> dict[str, Any]:
        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def publish_model_registered(self, model_id: str, name: str, version: str, module: str, created_by: str, tenant_id: str) -> None:
        event = type('ModelRegisteredEvent', (), {
            **self._create_base_event(),
            "model_id": model_id, "name": name, "version": version,
            "module": module, "created_by": created_by, "tenant_id": tenant_id
        })()
        await self._publish(event, "ModelRegistered")

    async def publish_model_promoted(self, model_id: str, name: str, from_stage: str, to_stage: str, approved_by: str, strategy: str, tenant_id: str) -> None:
        event = type('ModelPromotedEvent', (), {
            **self._create_base_event(),
            "model_id": model_id, "name": name, "from_stage": from_stage,
            "to_stage": to_stage, "approved_by": approved_by, "strategy": strategy, "tenant_id": tenant_id
        })()
        await self._publish(event, "ModelPromoted")

    async def publish_model_rejected(self, model_id: str, name: str, version: str, rejected_by: str, reason: str, tenant_id: str) -> None:
        event = type('ModelRejectedEvent', (), {
            **self._create_base_event(),
            "model_id": model_id, "name": name, "version": version,
            "rejected_by": rejected_by, "reason": reason, "tenant_id": tenant_id
        })()
        await self._publish(event, "ModelRejected")

    async def publish_feature_updated(self, feature_id: str, name: str, entity_type: str, source_module: str, version: int, tenant_id: str) -> None:
        event = type('FeatureUpdatedEvent', (), {
            **self._create_base_event(),
            "feature_id": feature_id, "name": name, "entity_type": entity_type,
            "source_module": source_module, "version": version, "tenant_id": tenant_id
        })()
        await self._publish(event, "FeatureUpdated")

    async def publish_drift_detected(self, model_id: str, drift_type: str, severity: str, drift_score: float, threshold: float, retraining_recommended: bool, tenant_id: str) -> None:
        event = type('DriftDetectedEvent', (), {
            **self._create_base_event(),
            "model_id": model_id, "drift_type": drift_type, "severity": severity,
            "drift_score": drift_score, "threshold": threshold, 
            "retraining_recommended": retraining_recommended, "tenant_id": tenant_id
        })()
        await self._publish(event, "DriftDetected")

    async def publish_retraining_started(self, job_id: str, model_id: str, trigger: str, feedback_count: int, tenant_id: str) -> None:
        event = type('RetrainingStartedEvent', (), {
            **self._create_base_event(),
            "job_id": job_id, "model_id": model_id, "trigger": trigger,
            "feedback_count": feedback_count, "tenant_id": tenant_id
        })()
        await self._publish(event, "RetrainingStarted")

    async def publish_retraining_completed(self, job_id: str, model_id: str, trigger: str, improvement_delta: float, new_version: str, tenant_id: str) -> None:
        event = type('RetrainingCompletedEvent', (), {
            **self._create_base_event(),
            "job_id": job_id, "model_id": model_id, "trigger": trigger,
            "improvement_delta": improvement_delta, "new_version": new_version, "tenant_id": tenant_id
        })()
        await self._publish(event, "RetrainingCompleted")

    async def publish_governance_alert(self, model_id: str, policy: str, violation_type: str, entity_id: str, confidence: float, tenant_id: str) -> None:
        event = type('GovernanceAlertEvent', (), {
            **self._create_base_event(),
            "model_id": model_id, "policy": policy, "violation_type": violation_type,
            "entity_id": entity_id, "confidence": confidence, "tenant_id": tenant_id
        })()
        await self._publish(event, "GovernanceAlert")

    async def publish_platform_health_changed(self, from_status: str, to_status: str, affected_components: list[str], active_alerts: list[str]) -> None:
        event = type('PlatformHealthChangedEvent', (), {
            **self._create_base_event(),
            "from_status": from_status, "to_status": to_status,
            "affected_components": affected_components, "active_alerts": active_alerts
        })()
        await self._publish(event, "PlatformHealthChanged")

    async def publish_deployment_completed(self, deployment_id: str, model_id: str, strategy: str, environment: str, traffic_pct: int, replicas: int, tenant_id: str) -> None:
        event = type('DeploymentCompletedEvent', (), {
            **self._create_base_event(),
            "deployment_id": deployment_id, "model_id": model_id, "strategy": strategy,
            "environment": environment, "traffic_pct": traffic_pct, "replicas": replicas, "tenant_id": tenant_id
        })()
        await self._publish(event, "DeploymentCompleted")

    async def publish_tenant_created(self, tenant_id: str, name: str, tier: str, max_plants: int) -> None:
        event = type('TenantCreatedEvent', (), {
            **self._create_base_event(),
            "tenant_id": tenant_id, "name": name, "tier": tier, "max_plants": max_plants
        })()
        await self._publish(event, "TenantCreated")

    async def publish_quota_exceeded(self, tenant_id: str, quota_type: str, used: float, limit: float) -> None:
        event = type('QuotaExceededEvent', (), {
            **self._create_base_event(),
            "tenant_id": tenant_id, "quota_type": quota_type, "used": used, "limit": limit
        })()
        await self._publish(event, "QuotaExceeded")
