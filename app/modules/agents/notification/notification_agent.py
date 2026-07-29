"""notification_agent.py — Notification Intelligence Agent (Milestone 3.9).

The Notification Agent is the communication layer of ABHEDYA.

It answers one question per event: "Who needs to know, how, and when?"

It transforms domain events from any ABHEDYA agent into:
  - Targeted notifications (right people)
  - Multi-channel delivery (right channel)
  - Timely dispatch (right time)
  - Confirmed receipt (acknowledgement)
  - Escalated alerts when unacknowledged
  - Suppressed duplicates during alert storms
  - Full audit trail for compliance

The Notification Agent never knows about RiskAgent, VisionAgent, or any
specific agent — it only understands domain events.
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.core.types import Capability
from app.modules.agents.notification.acknowledgement import AcknowledgementManager
from app.modules.agents.notification.audit import AuditTrail
from app.modules.agents.notification.deduplication import DeduplicationEngine
from app.modules.agents.notification.delivery_tracker import DeliveryTracker
from app.modules.agents.notification.dispatcher import ChannelDispatcher
from app.modules.agents.notification.escalation import EscalationEngine
from app.modules.agents.notification.events import NotificationEventGenerator
from app.modules.agents.notification.metrics import NotificationMetrics
from app.modules.agents.notification.models import NotificationAgentResult
from app.modules.agents.notification.orchestrator import NotificationOrchestrator
from app.modules.agents.notification.policy_engine import PolicyEngine
from app.modules.agents.notification.rate_limiter import RateLimiter
from app.modules.agents.notification.recipients import RecipientEngine
from app.modules.agents.notification.renderer import MessageRenderer
from app.modules.agents.notification.templates import TemplateRegistry

log = get_logger("agents.notification")


class NotificationAgent(BaseAgent):
    """
    Notification Intelligence Agent — Sprint 3 Milestone 3.9.

    Pipeline Phases:
      1. Policy Evaluation — determine severity, channels, ack requirements
      2. Deduplication   — suppress alert storms within sliding windows
      3. Recipient Resolution — resolve recipients from org hierarchy / roles
      4. Rate Limiting   — prevent notification spam per recipient
      5. Template Selection — match event type to message template
      6. Multi-Format Rendering — HTML, Markdown, plain text, rich cards
      7. Channel Dispatch — route to Email, SMS, Slack, Teams, Push, etc.
      8. Delivery Tracking — QUEUED → SENT → DELIVERED → ACKNOWLEDGED
      9. Acknowledgement Management — require confirmation for critical alerts
     10. Escalation — multi-level time-based escalation on timeout
     11. EventBus Publication — publish notification lifecycle events
     12. Audit Trail — compliance-grade log of every action
    """

    name: str = "NotificationAgent"
    version: str = "1.0.0"
    description: str = (
        "Transforms domain events into targeted multi-channel notifications "
        "with delivery tracking, acknowledgement management, escalation, and auditing."
    )
    capabilities: list[Capability] = [Capability.NOTIFICATION]

    def __init__(self) -> None:
        super().__init__()

        # Shared services (all injectable for testing)
        self.policy_engine = PolicyEngine()
        self.recipient_engine = RecipientEngine()
        self.template_registry = TemplateRegistry()
        self.renderer = MessageRenderer()
        self.dispatcher = ChannelDispatcher()
        self.deduplication = DeduplicationEngine()
        self.rate_limiter = RateLimiter()
        self.delivery_tracker = DeliveryTracker()
        self.ack_manager = AcknowledgementManager()
        self.escalation_engine = EscalationEngine()
        self.audit_trail = AuditTrail()
        self.metrics = NotificationMetrics()

        self.orchestrator = NotificationOrchestrator(
            policy_engine=self.policy_engine,
            recipient_engine=self.recipient_engine,
            template_registry=self.template_registry,
            renderer=self.renderer,
            dispatcher=self.dispatcher,
            deduplication=self.deduplication,
            rate_limiter=self.rate_limiter,
            delivery_tracker=self.delivery_tracker,
            ack_manager=self.ack_manager,
            escalation_engine=self.escalation_engine,
            audit_trail=self.audit_trail,
            metrics=self.metrics,
        )

    async def can_handle(self, context: AgentContext) -> bool:
        """Notification Agent can handle any context that contains domain events."""
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        """
        Execute the full notification pipeline for all incoming domain events.

        The context carries domain events via metadata["inbound_events"],
        or a single event_type is synthesized from context.query for demonstration.
        """
        # ─────────────────────────────────────────────────
        # 1. Collect inbound domain events
        # ─────────────────────────────────────────────────
        inbound_events = context.metadata.get("inbound_events", [])

        # Fallback: synthesize a demo event if none provided
        if not inbound_events:
            event_type = context.metadata.get("event_type", "RiskDetected")
            inbound_events = [
                AgentDomainEvent(
                    event_type=event_type,
                    agent_name="SyntheticSource",
                    payload=context.metadata.get("event_payload", {}),
                    trace_id=context.trace_id,
                )
            ]

        # ─────────────────────────────────────────────────
        # 2. Process each event through the orchestrator
        # ─────────────────────────────────────────────────
        zone_id = context.zone_id
        all_notifications = []
        all_domain_events: list[AgentDomainEvent] = []

        for event in inbound_events:
            # Ensure it's an AgentDomainEvent instance
            if isinstance(event, dict):
                event = AgentDomainEvent(**event)

            notifications, domain_events = await self.orchestrator.process_event(event, zone_id)
            all_notifications.extend(notifications)
            all_domain_events.extend(domain_events)

        # ─────────────────────────────────────────────────
        # 3. Aggregate result metrics
        # ─────────────────────────────────────────────────
        metrics_snapshot = self.metrics.snapshot()
        all_deliveries = []
        all_escalations = []
        for notif in all_notifications:
            all_deliveries.extend(notif.delivery_records)
            all_escalations.extend(notif.escalation_records)

        sent_count = sum(1 for d in all_deliveries if d.status.value == "SUCCESS")
        failed_count = sum(1 for d in all_deliveries if d.status.value == "FAILED")
        dedup_events = [e for e in all_domain_events if e.event_type == "NotificationDeduplicated"]

        # ─────────────────────────────────────────────────
        # 4. Build evidence and recommendations
        # ─────────────────────────────────────────────────
        evidence = [
            f"Processed {len(inbound_events)} inbound domain event(s)",
            f"Dispatched {sent_count} notifications successfully across "
            f"{len({d.provider for d in all_deliveries})} channel(s)",
            f"Delivery success rate: {metrics_snapshot['delivery_success_rate']:.1%}",
            f"Deduplicated {len(dedup_events)} alert storm event(s)",
            f"Pending acknowledgements: {self.ack_manager.get_pending_count()}",
            f"Audit trail entries: {self.audit_trail.total_entries()}",
        ]
        if failed_count > 0:
            evidence.append(f"{failed_count} delivery failure(s) recorded — retries scheduled.")

        recommendations = [
            "Monitor ABHEDYA Notification dashboard for unacknowledged critical alerts.",
            "Review escalation cascade if acknowledgement rates fall below 90%.",
            "Enable PagerDuty integration for EMERGENCY-severity events in production.",
        ]

        explanation = (
            f"Notification Agent processed {len(inbound_events)} event(s). "
            f"{sent_count}/{len(all_deliveries)} deliveries succeeded. "
            f"{self.ack_manager.get_pending_count()} alert(s) pending acknowledgement."
        )

        return NotificationAgentResult(
            agent_name=self.name,
            success=True,
            confidence=metrics_snapshot["delivery_success_rate"],
            evidence=evidence,
            recommendations=recommendations,
            events=all_domain_events,
            explanation=explanation,
            notifications_queued=len(all_notifications),
            notifications_sent=sent_count,
            notifications_deduplicated=len(dedup_events),
            notifications_failed=failed_count,
            notifications=all_notifications,
            delivery_records=all_deliveries,
            escalation_records=all_escalations,
            output_data={
                "metrics": metrics_snapshot,
                "notifications_count": len(all_notifications),
                "pending_acks": self.ack_manager.get_pending_count(),
                "audit_entries": self.audit_trail.total_entries(),
            },
        )
