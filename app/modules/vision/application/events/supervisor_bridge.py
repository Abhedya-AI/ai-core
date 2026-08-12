"""
vision/application/events/supervisor_bridge.py — Vision Supervisor Bridge.
"""
from __future__ import annotations
from typing import Any
from app.core.logging import get_logger
from app.modules.vision.domain.entities.detection_event import DetectionEvent, AlertSeverity
from app.modules.vision.domain.entities.vision_alert import VisionAlert

log = get_logger("vision.application.events.supervisor_bridge")

CRITICAL_CONFIDENCE_THRESHOLD = 0.65

class VisionSupervisorBridge:
    def __init__(self) -> None:
        self._engine = None
        self._available = False
        self._submission_count = 0
        self._failure_count = 0

    def _get_engine(self) -> Any:
        try:
            from app.modules.supervisor.supervisor_decision_engine import SupervisorDecisionEngine
            from app.modules.supervisor.capability_registry import CapabilityRegistry
            from app.modules.supervisor.agent_registry import AgentRegistry
            from app.modules.supervisor.parallel_executor import ParallelAgentExecutor
            from app.modules.supervisor.dependency_resolution import DependencyResolver
            from app.modules.supervisor.response_aggregation import ResponseAggregator
            from app.modules.supervisor.failure_recovery import FailureRecoveryManager
            from app.modules.supervisor.execution_history import SupervisorExecutionHistory
            
            if self._engine is None:
                cap_reg = CapabilityRegistry()
                agent_reg = AgentRegistry()
                dep_res = DependencyResolver()
                executor = ParallelAgentExecutor()
                aggregator = ResponseAggregator()
                recovery = FailureRecoveryManager()
                history = SupervisorExecutionHistory()
                self._engine = SupervisorDecisionEngine(
                    capability_registry=cap_reg,
                    agent_registry=agent_reg,
                    dependency_resolver=dep_res,
                    executor=executor,
                    aggregator=aggregator,
                    recovery_manager=recovery,
                    history=history,
                )
            self._available = True
            return self._engine
        except Exception as exc:
            log.warning(f"SupervisorDecisionEngine unavailable: {exc}")
            self._available = False
            return None

    def _should_submit(self, det_event: DetectionEvent) -> bool:
        hazard = det_event.hazard_type.value if hasattr(det_event.hazard_type, 'value') else str(det_event.hazard_type)
        severity = det_event.severity.value if hasattr(det_event.severity, 'value') else str(det_event.severity)
        
        if hazard in ('FIRE', 'SMOKE', 'CHEMICAL_SPILL', 'FALL'):
            return True
        if det_event.is_restricted_zone:
            return True
        if det_event.is_ppe_violation and det_event.confidence >= CRITICAL_CONFIDENCE_THRESHOLD:
            return True
        if severity == 'CRITICAL':
            return True
        return False

    def _build_agent_domain_event(self, det_event: DetectionEvent) -> Any:
        from app.modules.agents.core.events import AgentDomainEvent
        return AgentDomainEvent(
            event_type=det_event.stream_event_type.value if hasattr(det_event.stream_event_type, 'value') else str(det_event.stream_event_type),
            source="vision",
            payload={
                "detection_id": det_event.detection_id,
                "camera_id": det_event.camera_id,
                "zone_id": det_event.zone_id,
                "plant_id": det_event.plant_id,
                "hazard_type": det_event.hazard_type.value if hasattr(det_event.hazard_type, 'value') else str(det_event.hazard_type),
                "confidence": det_event.confidence,
                "risk_score": det_event.risk_score,
                "risk_level": det_event.risk_level.value if hasattr(det_event.risk_level, 'value') else str(det_event.risk_level),
                "severity": det_event.severity.value if hasattr(det_event.severity, 'value') else str(det_event.severity),
                "is_ppe_violation": det_event.is_ppe_violation,
                "is_restricted_zone": det_event.is_restricted_zone,
                "track_id": det_event.track_id,
                "detected_at": det_event.detected_at.isoformat() if det_event.detected_at else None,
            }
        )

    def _build_agent_context(self, det_event: DetectionEvent) -> Any:
        from app.modules.agents.core.agent_context import AgentContext
        hazard = det_event.hazard_type.value if hasattr(det_event.hazard_type, 'value') else str(det_event.hazard_type)
        return AgentContext(
            query=f"Vision alert: {hazard} detected in zone {det_event.zone_id} with {det_event.confidence:.1%} confidence.",
            zone_id=det_event.zone_id or "UNKNOWN",
            metadata={
                "source": "vision",
                "camera_id": det_event.camera_id,
                "detection_id": det_event.detection_id,
                "hazard_type": hazard,
                "risk_level": det_event.risk_level.value if hasattr(det_event.risk_level, 'value') else str(det_event.risk_level),
                "severity": det_event.severity.value if hasattr(det_event.severity, 'value') else str(det_event.severity),
            }
        )

    async def submit_detection_event(self, det_event: DetectionEvent) -> dict | None:
        if not self._should_submit(det_event):
            return None
        engine = self._get_engine()
        if not engine:
            return None
        
        try:
            agent_event = self._build_agent_domain_event(det_event)
            context = self._build_agent_context(det_event)
            assessment = await engine.process_event(agent_event, context)
            self._submission_count += 1
            return assessment.model_dump() if hasattr(assessment, 'model_dump') else assessment
        except Exception as exc:
            log.error(f"Failed to submit detection to supervisor: {exc}")
            self._failure_count += 1
            return None

    async def submit_alert(self, alert: VisionAlert, zone_id: str | None = None) -> dict | None:
        severity = alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity)
        if severity not in ('CRITICAL', 'HIGH'):
            return None
        engine = self._get_engine()
        if not engine:
            return None
        
        try:
            from app.modules.agents.core.events import AgentDomainEvent
            from app.modules.agents.core.agent_context import AgentContext
            
            agent_event = AgentDomainEvent(
                event_type="VISION_ALERT",
                source="vision",
                payload={"alert_id": alert.alert_id, "type": alert.alert_type, "severity": severity}
            )
            context = AgentContext(
                query=f"Vision Alert {alert.alert_type} in {alert.zone_id}",
                zone_id=alert.zone_id or zone_id or "UNKNOWN",
                metadata={"alert_id": alert.alert_id, "severity": severity}
            )
            assessment = await engine.process_event(agent_event, context)
            self._submission_count += 1
            return assessment.model_dump() if hasattr(assessment, 'model_dump') else assessment
        except Exception as exc:
            log.error(f"Failed to submit alert to supervisor: {exc}")
            self._failure_count += 1
            return None

    def get_stats(self) -> dict:
        return {
            "available": self._available,
            "submission_count": self._submission_count,
            "failure_count": self._failure_count
        }
