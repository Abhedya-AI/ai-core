"""orchestrator.py — Notification Orchestrator (Entry Point).

Implements the full notification workflow:

  Event → Policy Evaluation → Recipient Resolution → Deduplication →
  Rate Limiting → Template Selection → Rendering → Dispatch →
  Delivery Tracking → Acknowledgement Management → Escalation → Audit
"""

import uuid
from typing import Any

from app.core.logging import get_logger
from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.notification.acknowledgement import AcknowledgementManager
from app.modules.agents.notification.audit import AuditTrail
from app.modules.agents.notification.deduplication import DeduplicationEngine
from app.modules.agents.notification.delivery_tracker import DeliveryTracker
from app.modules.agents.notification.dispatcher import ChannelDispatcher
from app.modules.agents.notification.escalation import EscalationEngine
from app.modules.agents.notification.events import NotificationEventGenerator
from app.modules.agents.notification.metrics import NotificationMetrics
from app.modules.agents.notification.models import (
    Notification,
    NotificationStatus,
)
from app.modules.agents.notification.policy_engine import PolicyEngine
from app.modules.agents.notification.rate_limiter import RateLimiter
from app.modules.agents.notification.recipients import RecipientEngine
from app.modules.agents.notification.renderer import MessageRenderer
from app.modules.agents.notification.templates import TemplateRegistry

log = get_logger("agents.notification.orchestrator")


class NotificationOrchestrator:
    """
    Central orchestrator for the Notification Intelligence Agent.

    Responsibilities:
      1. Validate inbound domain event.
      2. Evaluate notification policy.
      3. Identify and resolve recipients.
      4. Deduplicate alert storms.
      5. Apply per-recipient rate limits.
      6. Select template and render channel-specific messages.
      7. Dispatch through channel providers.
      8. Track delivery status.
      9. Register pending acknowledgements for critical alerts.
      10. Trigger escalation if acknowledgement times out.
      11. Publish notification events back to EventBus.
      12. Maintain audit trail and metrics.
    """

    def __init__(
        self,
        policy_engine: PolicyEngine | None = None,
        recipient_engine: RecipientEngine | None = None,
        template_registry: TemplateRegistry | None = None,
        renderer: MessageRenderer | None = None,
        dispatcher: ChannelDispatcher | None = None,
        deduplication: DeduplicationEngine | None = None,
        rate_limiter: RateLimiter | None = None,
        delivery_tracker: DeliveryTracker | None = None,
        ack_manager: AcknowledgementManager | None = None,
        escalation_engine: EscalationEngine | None = None,
        audit_trail: AuditTrail | None = None,
        metrics: NotificationMetrics | None = None,
    ) -> None:
        self.policy_engine = policy_engine or PolicyEngine()
        self.recipient_engine = recipient_engine or RecipientEngine()
        self.template_registry = template_registry or TemplateRegistry()
        self.renderer = renderer or MessageRenderer()
        self.dispatcher = dispatcher or ChannelDispatcher()
        self.deduplication = deduplication or DeduplicationEngine()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.delivery_tracker = delivery_tracker or DeliveryTracker()
        self.ack_manager = ack_manager or AcknowledgementManager()
        self.escalation_engine = escalation_engine or EscalationEngine()
        self.audit_trail = audit_trail or AuditTrail()
        self.metrics = metrics or NotificationMetrics()

    async def process_event(
        self,
        event: AgentDomainEvent,
        zone_id: str | None = None,
    ) -> tuple[list[Notification], list[AgentDomainEvent]]:
        """
        Process an inbound domain event through the full notification pipeline.

        Args:
            event: Domain event from any ABHEDYA agent.
            zone_id: Optional zone context for recipient resolution.

        Returns:
            Tuple of (processed Notifications, published domain events).
        """
        log.info(f"NotificationOrchestrator: processing event '{event.event_type}' (trace={event.trace_id})")

        # ─────────────────────────────────────────────────
        # Step 1 — Policy Evaluation
        # ─────────────────────────────────────────────────
        policy = self.policy_engine.evaluate(event.event_type, event.payload)

        if not policy.should_notify:
            log.debug(f"Policy suppressed notification for event '{event.event_type}'")
            return [], []

        # ─────────────────────────────────────────────────
        # Step 2 — Deduplication
        # ─────────────────────────────────────────────────
        is_dup, dup_count = self.deduplication.is_duplicate(event.event_type, zone_id)
        if is_dup:
            self.metrics.record_deduplicated()
            self.audit_trail.log_deduplicated(event.id, event.event_type, dup_count, event.trace_id)
            dedup_event = NotificationEventGenerator.notification_deduplicated(
                "NotificationAgent", event.event_type, dup_count, event.trace_id
            )
            log.info(
                f"NotificationOrchestrator: deduplicated '{event.event_type}' "
                f"(suppressed_count={dup_count})"
            )
            return [], [dedup_event]

        # ─────────────────────────────────────────────────
        # Step 3 — Recipient Resolution
        # ─────────────────────────────────────────────────
        recipients = self.recipient_engine.resolve(event.event_type, policy.severity, zone_id)
        if not recipients:
            log.warning(f"No recipients resolved for event '{event.event_type}' — skipping.")
            return [], []

        # ─────────────────────────────────────────────────
        # Step 4 — Template Selection
        # ─────────────────────────────────────────────────
        template = self.template_registry.get_template(event.event_type)

        # Build template variables from event payload
        variables = _build_variables(event)

        # ─────────────────────────────────────────────────
        # Step 5 — Build & Register Notification
        # ─────────────────────────────────────────────────
        notification = Notification(
            event_id=event.id,
            event_type=event.event_type,
            severity=policy.severity,
            status=NotificationStatus.QUEUED,
            recipients=recipients,
            channels=policy.channels,
            requires_acknowledgement=policy.requires_acknowledgement,
            dedup_group_key=self.deduplication.build_group_key(event.event_type, zone_id),
        )
        self.delivery_tracker.register(notification)
        self.audit_trail.log_queued(notification, trace_id=event.trace_id)

        published_events: list[AgentDomainEvent] = []
        published_events.append(
            NotificationEventGenerator.notification_queued(
                "NotificationAgent", notification, event.trace_id
            )
        )

        # ─────────────────────────────────────────────────
        # Step 6 — Render & Dispatch per Recipient × Channel
        # ─────────────────────────────────────────────────
        all_deliveries = []
        for recipient in recipients:
            # Filter to channels preferred by the recipient
            target_channels = [
                ch for ch in policy.channels
                if ch in recipient.preferred_channels or ch.value in ("DASHBOARD",)
            ]
            # Fallback: use first available channel if no preference matches
            if not target_channels:
                target_channels = policy.channels[:1]

            for channel in target_channels:
                # Rate limiting check
                if not self.rate_limiter.is_allowed(
                    recipient.recipient_id, channel, policy.severity
                ):
                    self.metrics.record_rate_limited()
                    self.audit_trail.log_rate_limited(
                        notification.notification_id,
                        event.event_type,
                        recipient.recipient_id,
                        channel.value,
                        event.trace_id,
                    )
                    continue

                # Render message for channel
                rendered = self.renderer.render(template, channel, dict(variables), locale=recipient.locale)

                # Dispatch
                delivery = await self.dispatcher.dispatch(rendered, recipient, notification.notification_id)
                all_deliveries.append(delivery)
                self.delivery_tracker.record_delivery(delivery)
                self.audit_trail.log_delivery(delivery, event.event_type, event.trace_id)

                if delivery.status.value == "SUCCESS":
                    self.metrics.record_sent(channel.value, event.event_type)
                    published_events.append(
                        NotificationEventGenerator.notification_sent(
                            "NotificationAgent", notification, delivery, event.trace_id
                        )
                    )
                else:
                    self.metrics.record_failed(channel.value)
                    published_events.append(
                        NotificationEventGenerator.notification_failed(
                            "NotificationAgent", notification, delivery, event.trace_id
                        )
                    )

        notification.delivery_records = all_deliveries

        # ─────────────────────────────────────────────────
        # Step 7 — Acknowledgement Registration
        # ─────────────────────────────────────────────────
        if policy.requires_acknowledgement:
            self.ack_manager.register_pending(notification.notification_id)

        log.info(
            f"NotificationOrchestrator: '{event.event_type}' → "
            f"{len(all_deliveries)} delivery attempt(s), "
            f"ack_required={policy.requires_acknowledgement}"
        )

        return [notification], published_events

    async def process_escalation(
        self,
        notification: Notification,
        escalation_policy_id: str,
        trace_id: str,
    ) -> list[AgentDomainEvent]:
        """
        Check for overdue acknowledgements and escalate if needed.

        Args:
            notification: Notification to evaluate.
            escalation_policy_id: Policy ID (e.g. 'escalation_critical').
            trace_id: Originating trace context.

        Returns:
            Domain events generated during escalation.
        """
        if not self.ack_manager.is_overdue(notification.notification_id):
            return []

        if not self.escalation_engine.needs_escalation(
            notification.notification_id, escalation_policy_id
        ):
            return []

        current_level = self.escalation_engine.current_level(notification.notification_id)
        next_level = current_level + 1

        # Resolve escalation recipient
        escalation_recipient = self.recipient_engine.resolve_escalation_level(
            escalation_policy_id, next_level
        )
        if not escalation_recipient:
            log.warning(
                f"No escalation recipient at level {next_level} "
                f"for policy '{escalation_policy_id}'"
            )
            return []

        record, escalation_channels = self.escalation_engine.escalate(
            notification.notification_id,
            escalation_policy_id,
            escalation_recipient.user_id,
        )

        self.metrics.record_escalation()
        self.audit_trail.log_escalation(record, notification.event_type, trace_id)

        # Dispatch escalation message
        template = self.template_registry.get_template(notification.event_type)
        variables = {"event_type": notification.event_type, "zone": "N/A", "incident_id": notification.notification_id}

        events: list[AgentDomainEvent] = []
        for channel in escalation_channels:
            rendered = self.renderer.render(template, channel, dict(variables))
            delivery = await self.dispatcher.dispatch(rendered, escalation_recipient, notification.notification_id)
            self.delivery_tracker.record_delivery(delivery)

        events.append(
            NotificationEventGenerator.notification_escalated("NotificationAgent", record, trace_id)
        )
        notification.escalation_records.append(record)
        return events


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_variables(event: AgentDomainEvent) -> dict:
    """Extract template variables from a domain event payload."""
    payload = event.payload
    return {
        "event_type": event.event_type,
        "incident_id": event.id,
        "trace_id": event.trace_id,
        "zone": payload.get("zone_id", payload.get("target_zone", payload.get("zone", "N/A"))),
        "asset": payload.get("asset_id", payload.get("equipment_id", "N/A")),
        "risk_score": payload.get("risk_score", payload.get("score_value", "N/A")),
        "confidence": payload.get("confidence", "N/A"),
        "workers": ", ".join(str(w) for w in payload.get("affected_workers", [])) or "N/A",
        "recommendation": payload.get("recommendation", "Refer to ABHEDYA dashboard."),
        "severity": payload.get("severity", "N/A"),
        "actions": payload.get("actions", []),
        "plan_id": payload.get("plan_id", "N/A"),
        "action_count": payload.get("action_count", 0),
        "assets": payload.get("assets", payload.get("asset_id", "N/A")),
        "regulation": payload.get("regulation", "N/A"),
        "violation": payload.get("violation", "N/A"),
        "probability": payload.get("failure_probability", "N/A"),
        "horizon": payload.get("horizon", "N/A"),
        "permit_id": payload.get("permit_id", "N/A"),
        "details": str(payload)[:200],
    }
