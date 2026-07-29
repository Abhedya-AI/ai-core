"""test_notification_agent.py — Comprehensive tests for Milestone 3.9: Notification Intelligence Agent.

Tests cover:
  - Policy Engine: event → severity / channel / ack mapping
  - Recipient Engine: role-based resolution and escalation cascade
  - Template Registry and Renderer: multi-format rendering
  - Deduplication: alert storm suppression
  - Rate Limiter: per-recipient limits with emergency bypass
  - Dispatcher & Providers: common interface contract
  - Delivery Tracker: full lifecycle tracking
  - Acknowledgement Manager: pending/overdue/confirmed states
  - Escalation Engine: multi-level time-based escalation
  - Audit Trail: append-only compliance log
  - Metrics: operational observability snapshot
  - NotificationAgent end-to-end: full pipeline including dedup, ack, escalation
"""

import pytest

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.notification import (
    Notification,
    NotificationAgent,
    NotificationChannel,
    NotificationOrchestrator,
    NotificationSeverity,
    NotificationStatus,
)
from app.modules.agents.notification.acknowledgement import AcknowledgementManager
from app.modules.agents.notification.audit import AuditTrail
from app.modules.agents.notification.deduplication import DeduplicationEngine
from app.modules.agents.notification.delivery_tracker import DeliveryTracker
from app.modules.agents.notification.dispatcher import (
    ChannelDispatcher,
    DashboardProvider,
    EmailProvider,
    PushProvider,
    SMSProvider,
    SlackProvider,
)
from app.modules.agents.notification.escalation import EscalationEngine
from app.modules.agents.notification.metrics import NotificationMetrics
from app.modules.agents.notification.models import (
    DeliveryRecord,
    DeliveryStatus,
    RecipientProfile,
    RenderedMessage,
)
from app.modules.agents.notification.policy_engine import PolicyEngine
from app.modules.agents.notification.rate_limiter import RateLimiter
from app.modules.agents.notification.recipients import RecipientEngine
from app.modules.agents.notification.renderer import MessageRenderer
from app.modules.agents.notification.templates import TemplateRegistry


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Policy Engine — severity mapping, channel selection, ack requirements
# ─────────────────────────────────────────────────────────────────────────────

def test_policy_engine_severity_and_channels():
    """PolicyEngine maps each event type to correct severity and channels."""
    engine = PolicyEngine()

    # FireDetected → EMERGENCY, requires ack, includes SMS + PAGERDUTY
    result = engine.evaluate("FireDetected", {})
    assert result.severity == NotificationSeverity.EMERGENCY
    assert result.requires_acknowledgement is True
    assert NotificationChannel.SMS in result.channels
    assert NotificationChannel.PAGERDUTY in result.channels

    # RiskDetected → MEDIUM, no ack, email + dashboard
    result = engine.evaluate("RiskDetected", {})
    assert result.severity == NotificationSeverity.MEDIUM
    assert result.requires_acknowledgement is False
    assert NotificationChannel.EMAIL in result.channels
    assert NotificationChannel.DASHBOARD in result.channels

    # DocumentIndexed → INFORMATIONAL, no ack, dashboard only
    result = engine.evaluate("DocumentIndexed", {})
    assert result.severity == NotificationSeverity.INFORMATIONAL
    assert result.requires_acknowledgement is False
    assert result.channels == [NotificationChannel.DASHBOARD]

    # Unknown event → should_notify=True with LOW default
    result = engine.evaluate("SomeUnknownEvent", {})
    assert result.should_notify is True
    assert result.severity == NotificationSeverity.LOW


def test_policy_engine_payload_severity_override():
    """PolicyEngine respects severity overrides embedded in event payload."""
    engine = PolicyEngine()
    # RiskDetected default = MEDIUM; payload severity=CRITICAL should upgrade
    result = engine.evaluate("RiskDetected", {"severity": "CRITICAL"})
    assert result.severity == NotificationSeverity.CRITICAL
    assert result.requires_acknowledgement is True


def test_policy_engine_escalation_policy_id():
    """PolicyEngine generates correct escalation_policy_id strings."""
    engine = PolicyEngine()
    result = engine.evaluate("HighRiskDetected", {})
    assert result.escalation_policy_id == "escalation_high"

    result = engine.evaluate("EmergencyPlanGenerated", {})
    assert result.escalation_policy_id == "escalation_emergency"


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Recipient Engine — role resolution and escalation cascade
# ─────────────────────────────────────────────────────────────────────────────

def test_recipient_engine_resolves_correct_roles():
    """RecipientEngine resolves correct role-based recipients for key events."""
    engine = RecipientEngine()

    # FireDetected should include safety_officer + fire_team_lead
    recipients = engine.resolve("FireDetected", NotificationSeverity.EMERGENCY)
    roles = {r.role for r in recipients}
    assert "SAFETY_OFFICER" in roles
    assert "FIRE_TEAM_LEAD" in roles
    assert "PLANT_MANAGER" in roles

    # PermitExpired → maintenance_supervisor + compliance_officer
    recipients = engine.resolve("PermitExpired", NotificationSeverity.HIGH)
    roles = {r.role for r in recipients}
    assert "MAINTENANCE_SUPERVISOR" in roles
    assert "COMPLIANCE_OFFICER" in roles

    # No duplicates in resolved list
    ids = [r.recipient_id for r in recipients]
    assert len(ids) == len(set(ids)), "Duplicate recipients returned"


def test_recipient_engine_escalation_cascade():
    """RecipientEngine escalation levels resolve in correct order."""
    engine = RecipientEngine()

    # Emergency escalation level 1 → shift_supervisor
    r1 = engine.resolve_escalation_level("escalation_emergency", 1)
    assert r1 is not None
    assert r1.role == "SHIFT_SUPERVISOR"

    # Level 2 → safety_officer
    r2 = engine.resolve_escalation_level("escalation_emergency", 2)
    assert r2 is not None
    assert r2.role == "SAFETY_OFFICER"

    # Level beyond max → None
    r_none = engine.resolve_escalation_level("escalation_emergency", 99)
    assert r_none is None


def test_recipient_engine_max_escalation_levels():
    """Max escalation levels are correctly bounded."""
    engine = RecipientEngine()
    assert engine.max_escalation_levels("escalation_emergency") == 4
    assert engine.max_escalation_levels("escalation_low") == 0
    assert engine.max_escalation_levels("escalation_informational") == 0


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Template Rendering — multi-format output with variable substitution
# ─────────────────────────────────────────────────────────────────────────────

def test_template_registry_lookup():
    """TemplateRegistry resolves templates for known and unknown events."""
    registry = TemplateRegistry()

    tpl = registry.get_template("FireDetected")
    assert tpl.event_type == "FireDetected"
    assert "🔥" in tpl.subject_template

    # Unknown event → _default template
    tpl_default = registry.get_template("SomeObscureEvent")
    assert tpl_default.template_id == "tpl_default"

    known = registry.list_supported_events()
    assert "FireDetected" in known
    assert "ComplianceViolationDetected" in known


def test_message_renderer_email_format():
    """MessageRenderer produces correct HTML body for email channel."""
    registry = TemplateRegistry()
    renderer = MessageRenderer()
    template = registry.get_template("HighRiskDetected")
    variables = {
        "risk_score": "87.5",
        "zone": "Zone-B",
        "workers": "W-101, W-102",
        "recommendation": "Evacuate immediately",
        "incident_id": "INC-001",
    }
    rendered = renderer.render(template, NotificationChannel.EMAIL, variables)
    assert rendered.channel == NotificationChannel.EMAIL
    assert "Zone-B" in rendered.body_text
    assert "Zone-B" in rendered.body_html
    assert "87.5" in rendered.body_html
    assert rendered.subject != ""
    assert "INC-001" in rendered.body_text


def test_message_renderer_sms_truncation():
    """MessageRenderer truncates SMS body to ≤ 160 characters."""
    registry = TemplateRegistry()
    renderer = MessageRenderer()
    template = registry.get_template("SmokeDetected")
    variables = {"zone": "Zone-A", "confidence": "0.97", "incident_id": "INC-002", "actions": []}
    rendered = renderer.render(template, NotificationChannel.SMS, variables)
    assert rendered.channel == NotificationChannel.SMS
    assert len(rendered.body_text) <= 160


def test_message_renderer_slack_rich_card():
    """MessageRenderer builds Slack block kit rich card."""
    registry = TemplateRegistry()
    renderer = MessageRenderer()
    template = registry.get_template("FireDetected")
    variables = {"zone": "Zone-C", "confidence": "0.99", "incident_id": "INC-003",
                 "assets": "PUMP-P12", "actions": ["Activate sprinklers"]}
    rendered = renderer.render(template, NotificationChannel.SLACK, variables)
    assert "blocks" in rendered.rich_card
    assert rendered.body_markdown != ""


def test_message_renderer_teams_adaptive_card():
    """MessageRenderer builds Teams Adaptive Card."""
    registry = TemplateRegistry()
    renderer = MessageRenderer()
    template = registry.get_template("EmergencyPlanGenerated")
    variables = {"zone": "Zone-D", "plan_id": "EP-42", "action_count": 5,
                 "incident_id": "INC-004", "actions": []}
    rendered = renderer.render(template, NotificationChannel.TEAMS, variables)
    assert rendered.rich_card.get("type") == "AdaptiveCard"


def test_message_renderer_list_actions():
    """MessageRenderer converts list actions to bullet-point and HTML formats."""
    registry = TemplateRegistry()
    renderer = MessageRenderer()
    template = registry.get_template("FireDetected")
    variables = {
        "zone": "Z1", "confidence": "0.9", "incident_id": "I1", "assets": "A1",
        "actions": ["Activate alarm", "Call fire team", "Evacuate zone"],
    }
    rendered = renderer.render(template, NotificationChannel.EMAIL, variables)
    assert "• Activate alarm" in rendered.body_text
    assert "<li>Activate alarm</li>" in rendered.body_html


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Deduplication and Rate Limiter
# ─────────────────────────────────────────────────────────────────────────────

def test_deduplication_first_occurrence_allowed():
    """DeduplicationEngine allows first occurrence of any event."""
    dedup = DeduplicationEngine(window_seconds=60)
    is_dup, count = dedup.is_duplicate("SmokeDetected", "Zone-A")
    assert is_dup is False
    assert count == 1


def test_deduplication_second_occurrence_suppressed():
    """DeduplicationEngine suppresses second occurrence within window."""
    dedup = DeduplicationEngine(window_seconds=60)
    dedup.is_duplicate("SmokeDetected", "Zone-A")  # first — allowed
    is_dup, count = dedup.is_duplicate("SmokeDetected", "Zone-A")  # second — suppressed
    assert is_dup is True
    assert count == 2


def test_deduplication_different_zones_independent():
    """DeduplicationEngine treats different zones as separate groups."""
    dedup = DeduplicationEngine(window_seconds=60)
    dedup.is_duplicate("SmokeDetected", "Zone-A")
    is_dup_b, _ = dedup.is_duplicate("SmokeDetected", "Zone-B")
    assert is_dup_b is False  # Zone-B is a new group


def test_deduplication_clear_group():
    """DeduplicationEngine can clear a group for explicit reset."""
    dedup = DeduplicationEngine(window_seconds=60)
    dedup.is_duplicate("FireDetected", "Zone-A")
    dedup.is_duplicate("FireDetected", "Zone-A")
    dedup.clear_group("FireDetected", "Zone-A")
    is_dup, count = dedup.is_duplicate("FireDetected", "Zone-A")
    assert is_dup is False
    assert count == 1


def test_rate_limiter_allows_within_limit():
    """RateLimiter permits sends within the configured threshold."""
    limiter = RateLimiter(max_per_window=5, window_seconds=60)
    for _ in range(5):
        allowed = limiter.is_allowed("RCP-001", NotificationChannel.EMAIL, NotificationSeverity.MEDIUM)
        assert allowed is True


def test_rate_limiter_blocks_over_limit():
    """RateLimiter blocks sends exceeding the threshold."""
    limiter = RateLimiter(max_per_window=3, window_seconds=60)
    for _ in range(3):
        limiter.is_allowed("RCP-002", NotificationChannel.EMAIL, NotificationSeverity.MEDIUM)
    blocked = limiter.is_allowed("RCP-002", NotificationChannel.EMAIL, NotificationSeverity.MEDIUM)
    assert blocked is False


def test_rate_limiter_emergency_bypass():
    """Emergency severity bypasses rate limit entirely."""
    limiter = RateLimiter(max_per_window=1, window_seconds=60)
    limiter.is_allowed("RCP-003", NotificationChannel.SMS, NotificationSeverity.LOW)
    limiter.is_allowed("RCP-003", NotificationChannel.SMS, NotificationSeverity.LOW)  # exceeds limit
    # Emergency should still pass
    allowed = limiter.is_allowed("RCP-003", NotificationChannel.SMS, NotificationSeverity.EMERGENCY)
    assert allowed is True


def test_rate_limiter_critical_bypass():
    """Critical severity also bypasses rate limiting."""
    limiter = RateLimiter(max_per_window=1, window_seconds=60)
    limiter.is_allowed("RCP-004", NotificationChannel.PUSH, NotificationSeverity.LOW)
    limiter.is_allowed("RCP-004", NotificationChannel.PUSH, NotificationSeverity.LOW)
    allowed = limiter.is_allowed("RCP-004", NotificationChannel.PUSH, NotificationSeverity.CRITICAL)
    assert allowed is True


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Dispatcher and Providers
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_all_providers_implement_contract():
    """All providers successfully send and return DeliveryResult."""
    recipient = RecipientProfile(
        user_id="U-TEST-01",
        name="Test User",
        preferred_channels=[NotificationChannel.EMAIL],
        email="test@plant.example",
        phone="+1-555-0000",
        push_token="push:test",
    )
    providers = [
        EmailProvider(), SMSProvider(), PushProvider(),
        SlackProvider(), DashboardProvider(),
    ]
    rendered = RenderedMessage(
        subject="Test Alert",
        body_text="This is a test notification.",
        channel=NotificationChannel.EMAIL,
    )
    for provider in providers:
        rendered_copy = rendered.model_copy(update={"channel": provider.channel})
        result = await provider.send(rendered_copy, recipient, "NOTIF-TEST-001")
        assert result.success is True
        assert result.provider_message_id is not None


@pytest.mark.asyncio
async def test_channel_dispatcher_routes_correctly():
    """ChannelDispatcher produces DeliveryRecord with correct provider and status."""
    dispatcher = ChannelDispatcher()
    recipient = RecipientProfile(
        user_id="U-DISP-01",
        name="Dispatch User",
        preferred_channels=[NotificationChannel.SLACK],
        push_token="push:dispatch",
    )
    rendered = RenderedMessage(
        subject="Dispatcher Test",
        body_text="Testing channel routing.",
        channel=NotificationChannel.SLACK,
    )
    record = await dispatcher.dispatch(rendered, recipient, "NOTIF-DISP-001")
    assert isinstance(record, DeliveryRecord)
    assert record.provider == NotificationChannel.SLACK
    assert record.status == DeliveryStatus.SUCCESS
    assert record.notification_id == "NOTIF-DISP-001"


@pytest.mark.asyncio
async def test_channel_dispatcher_unknown_channel():
    """ChannelDispatcher returns FAILED record for unregistered channel."""
    dispatcher = ChannelDispatcher()
    recipient = RecipientProfile(user_id="U-UNK-01", name="Unknown")
    # Use WEBSOCKET but manually remove from registry for test
    rendered = RenderedMessage(
        subject="Unknown Channel",
        body_text="No provider registered.",
        channel=NotificationChannel.WEBSOCKET,
    )
    # Remove provider temporarily
    from app.modules.agents.notification import dispatcher as disp_module
    backup = disp_module._PROVIDER_REGISTRY.pop(NotificationChannel.WEBSOCKET, None)
    record = await dispatcher.dispatch(rendered, recipient, "NOTIF-UNK-001")
    assert record.status == DeliveryStatus.FAILED
    # Restore
    if backup:
        disp_module._PROVIDER_REGISTRY[NotificationChannel.WEBSOCKET] = backup


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Delivery Tracker
# ─────────────────────────────────────────────────────────────────────────────

def test_delivery_tracker_lifecycle():
    """DeliveryTracker correctly manages QUEUED → SENT → ACKNOWLEDGED lifecycle."""
    tracker = DeliveryTracker()

    notif = Notification(
        event_id="EVT-001",
        event_type="HighRiskDetected",
        severity=NotificationSeverity.HIGH,
        requires_acknowledgement=True,
    )
    tracker.register(notif)
    assert tracker.get_notification(notif.notification_id) is not None
    assert notif.status == NotificationStatus.QUEUED

    # Record a successful delivery
    delivery = DeliveryRecord(
        notification_id=notif.notification_id,
        recipient_id="RCP-001",
        provider=NotificationChannel.SMS,
        status=DeliveryStatus.SUCCESS,
    )
    tracker.record_delivery(delivery)
    assert notif.status == NotificationStatus.SENT

    # Acknowledge
    result = tracker.mark_acknowledged(notif.notification_id, "Alex Chen")
    assert result is True
    assert notif.status == NotificationStatus.ACKNOWLEDGED

    # Pending acknowledgements should be empty
    pending = tracker.pending_acknowledgements()
    assert notif not in pending


def test_delivery_tracker_pending_acknowledgements():
    """DeliveryTracker correctly identifies notifications awaiting acknowledgement."""
    tracker = DeliveryTracker()
    notif = Notification(
        event_id="EVT-002",
        event_type="FireDetected",
        severity=NotificationSeverity.EMERGENCY,
        requires_acknowledgement=True,
    )
    tracker.register(notif)

    delivery = DeliveryRecord(
        notification_id=notif.notification_id,
        recipient_id="RCP-002",
        provider=NotificationChannel.PUSH,
        status=DeliveryStatus.SUCCESS,
    )
    tracker.record_delivery(delivery)

    pending = tracker.pending_acknowledgements()
    assert any(n.notification_id == notif.notification_id for n in pending)


def test_delivery_tracker_unknown_notification():
    """DeliveryTracker returns False for unknown notification acknowledgement."""
    tracker = DeliveryTracker()
    result = tracker.mark_acknowledged("NON-EXISTENT-ID", "Nobody")
    assert result is False


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Acknowledgement Manager
# ─────────────────────────────────────────────────────────────────────────────

def test_ack_manager_register_and_acknowledge():
    """AcknowledgementManager correctly tracks pending and acknowledged notifications."""
    ack = AcknowledgementManager(ack_timeout_seconds=300)
    nid = "NOTIF-ACK-001"

    ack.register_pending(nid)
    assert not ack.is_acknowledged(nid)
    assert not ack.is_overdue(nid)

    record = ack.acknowledge(nid, acknowledged_by="Priya Nair")
    assert ack.is_acknowledged(nid)
    assert record.acknowledged_by == "Priya Nair"
    assert not ack.is_overdue(nid)


def test_ack_manager_pending_count():
    """AcknowledgementManager counts pending notifications correctly."""
    ack = AcknowledgementManager()
    ack.register_pending("N-001")
    ack.register_pending("N-002")
    assert ack.get_pending_count() == 2
    ack.acknowledge("N-001", "User A")
    assert ack.get_pending_count() == 1


def test_ack_manager_overdue_detection():
    """AcknowledgementManager detects overdue notifications via monotonic clock override."""
    import time
    ack = AcknowledgementManager(ack_timeout_seconds=0)
    nid = "NOTIF-OVERDUE-001"
    ack.register_pending(nid)

    # Manually force the deadline to be in the past
    ack._pending[nid] = time.monotonic() - 1

    assert ack.is_overdue(nid)
    overdue = ack.get_overdue_notifications()
    assert nid in overdue


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: Escalation Engine
# ─────────────────────────────────────────────────────────────────────────────

def test_escalation_engine_multi_level():
    """EscalationEngine advances through levels and records correctly."""
    engine = EscalationEngine()
    nid = "NOTIF-ESC-001"
    policy = "escalation_critical"

    assert engine.needs_escalation(nid, policy) is True
    assert engine.current_level(nid) == 0

    record1, channels1 = engine.escalate(nid, policy, "shift_supervisor")
    assert record1.level == 1
    assert engine.current_level(nid) == 1
    assert len(channels1) > 0

    record2, channels2 = engine.escalate(nid, policy, "safety_officer")
    assert record2.level == 2

    records = engine.get_records(nid)
    assert len(records) == 2
    assert records[0].escalated_to == "shift_supervisor"
    assert records[1].escalated_to == "safety_officer"


def test_escalation_engine_no_escalation_for_low():
    """EscalationEngine does not escalate LOW/INFORMATIONAL policies."""
    engine = EscalationEngine()
    assert engine.needs_escalation("N-001", "escalation_low") is False
    assert engine.needs_escalation("N-002", "escalation_informational") is False


def test_escalation_engine_max_levels_respected():
    """EscalationEngine stops escalating after max levels are reached."""
    engine = EscalationEngine()
    nid = "NOTIF-MAX-001"
    policy = "escalation_medium"

    # escalation_medium has 1 level
    engine.escalate(nid, policy, "shift_supervisor")
    assert engine.needs_escalation(nid, policy) is False


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: Audit Trail
# ─────────────────────────────────────────────────────────────────────────────

def test_audit_trail_append_and_query():
    """AuditTrail logs all lifecycle actions and allows filtered retrieval."""
    audit = AuditTrail()
    notif = Notification(
        event_id="EVT-AUDIT-001",
        event_type="SmokeDetected",
        severity=NotificationSeverity.CRITICAL,
    )
    audit.log_queued(notif, trace_id="TRACE-001")
    assert audit.total_entries() == 1

    delivery = DeliveryRecord(
        notification_id=notif.notification_id,
        recipient_id="RCP-A",
        provider=NotificationChannel.SMS,
        status=DeliveryStatus.SUCCESS,
    )
    audit.log_delivery(delivery, "SmokeDetected", "TRACE-001")
    assert audit.total_entries() == 2

    entries = audit.get_entries(notif.notification_id)
    assert len(entries) == 2
    actions = {e["action"] for e in entries}
    assert "QUEUED" in actions
    assert "DELIVERY_SUCCESS" in actions


def test_audit_trail_all_action_types():
    """AuditTrail covers all notification lifecycle log methods."""
    audit = AuditTrail()
    from app.modules.agents.notification.models import AcknowledgementRecord, EscalationRecord

    nid = "N-AUDIT-ALL"
    ack = AcknowledgementRecord(notification_id=nid, acknowledged_by="Test User")
    escalation = EscalationRecord(notification_id=nid, level=2, escalated_to="plant_manager")

    audit.log_acknowledgement(ack, trace_id="T1")
    audit.log_escalation(escalation, trace_id="T1")
    audit.log_deduplicated(nid, "FireDetected", count=5)
    audit.log_rate_limited(nid, "FireDetected", "RCP-001", "SMS")

    entries = audit.get_entries(nid)
    actions = {e["action"] for e in entries}
    assert "ACKNOWLEDGED" in actions
    assert "ESCALATED_LEVEL_2" in actions
    assert "DEDUPLICATED" in actions
    assert "RATE_LIMITED" in actions


# ─────────────────────────────────────────────────────────────────────────────
# Test 10: Notification Metrics
# ─────────────────────────────────────────────────────────────────────────────

def test_metrics_snapshot_accuracy():
    """NotificationMetrics tracks all counters and computes derived rates."""
    m = NotificationMetrics()

    m.record_sent("EMAIL", "RiskDetected")
    m.record_sent("SMS", "FireDetected")
    m.record_failed("PUSH")
    m.record_deduplicated()
    m.record_rate_limited()
    m.record_escalation()
    m.record_acknowledgement(latency_seconds=45.0)

    snap = m.snapshot()
    assert snap["notifications_sent"] == 2
    assert snap["notifications_failed"] == 1
    assert snap["notifications_deduplicated"] == 1
    assert snap["notifications_rate_limited"] == 1
    assert snap["escalations"] == 1
    assert snap["acknowledgements"] == 1
    assert snap["avg_ack_latency_seconds"] == 45.0
    assert snap["delivery_success_rate"] == pytest.approx(2 / 3, rel=0.01)
    assert snap["duplicate_suppression_rate"] == pytest.approx(1 / 3, rel=0.01)
    assert "EMAIL" in snap["channel_success"]
    assert snap["event_type_counts"]["FireDetected"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 11: NotificationAgent End-to-End Execution
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notification_agent_fire_detection_pipeline():
    """Full pipeline: FireDetected event → multi-channel delivery → ack pending."""
    agent = NotificationAgent()
    fire_event = AgentDomainEvent(
        event_type="FireDetected",
        agent_name="VisionAgent",
        payload={
            "zone_id": "Zone-B",
            "confidence": "0.98",
            "assets": "PUMP-P12, TANK-T04",
            "actions": ["Activate sprinkler system", "Evacuate Zone-B", "Call fire team"],
        },
    )
    context = AgentContext(
        query="FireDetected event",
        metadata={"inbound_events": [fire_event.model_dump()]},
    )
    result = await agent.execute(context)
    assert result.success is True
    assert result.agent_name == "NotificationAgent"
    assert result.output_data["notifications_count"] >= 1
    assert result.output_data["pending_acks"] >= 1
    assert result.output_data["audit_entries"] > 0
    assert len(result.events) > 0

    # Check NotificationQueued event was published
    event_types = {e.event_type for e in result.events}
    assert "NotificationQueued" in event_types


@pytest.mark.asyncio
async def test_notification_agent_multi_event_batch():
    """NotificationAgent processes a batch of multiple events from different agents."""
    agent = NotificationAgent()

    events = [
        AgentDomainEvent(
            event_type="SmokeDetected",
            agent_name="VisionAgent",
            payload={"zone_id": "Zone-A", "confidence": "0.95"},
        ),
        AgentDomainEvent(
            event_type="HighRiskDetected",
            agent_name="RiskAgent",
            payload={"risk_score": 85.0, "zone_id": "Zone-A", "severity": "HIGH"},
        ),
        AgentDomainEvent(
            event_type="EquipmentFailurePredicted",
            agent_name="PredictionAgent",
            payload={"asset_id": "PUMP-P12", "failure_probability": 0.87, "horizon": "24h"},
        ),
    ]

    context = AgentContext(
        query="Multi-event batch",
        metadata={"inbound_events": [e.model_dump() for e in events]},
    )
    result = await agent.execute(context)

    assert result.success is True
    assert result.output_data["notifications_count"] == 3
    event_types = {e.event_type for e in result.events}
    assert "NotificationQueued" in event_types
    assert "NotificationSent" in event_types


@pytest.mark.asyncio
async def test_notification_agent_deduplication_in_pipeline():
    """NotificationAgent suppresses duplicate events in the same batch."""
    agent = NotificationAgent()

    events = [
        AgentDomainEvent(event_type="SmokeDetected", agent_name="VisionAgent",
                         payload={"zone_id": "Zone-C"}),
        AgentDomainEvent(event_type="SmokeDetected", agent_name="VisionAgent",
                         payload={"zone_id": "Zone-C"}),
        AgentDomainEvent(event_type="SmokeDetected", agent_name="VisionAgent",
                         payload={"zone_id": "Zone-C"}),
    ]

    context = AgentContext(
        query="Smoke storm dedup test",
        metadata={"inbound_events": [e.model_dump() for e in events]},
    )
    result = await agent.execute(context)

    assert result.success is True
    dedup_events = [e for e in result.events if e.event_type == "NotificationDeduplicated"]
    assert len(dedup_events) >= 2  # 2nd and 3rd events should be deduplicated


@pytest.mark.asyncio
async def test_notification_agent_informational_event_no_ack():
    """Informational events are dispatched without requiring acknowledgement."""
    agent = NotificationAgent()
    context = AgentContext(
        query="Document indexed",
        metadata={
            "inbound_events": [
                AgentDomainEvent(
                    event_type="DocumentIndexed",
                    agent_name="DocumentAgent",
                    payload={"doc_id": "SOP-HS-04"},
                ).model_dump()
            ]
        },
    )
    result = await agent.execute(context)
    assert result.success is True
    assert result.output_data["pending_acks"] == 0


@pytest.mark.asyncio
async def test_notification_agent_default_fallback_event():
    """NotificationAgent handles context with no inbound_events via synthetic fallback."""
    agent = NotificationAgent()
    context = AgentContext(
        query="Run notification agent",
        metadata={"event_type": "RiskDetected", "event_payload": {"zone_id": "Zone-D"}},
    )
    result = await agent.execute(context)
    assert result.success is True
    assert result.agent_name == "NotificationAgent"


@pytest.mark.asyncio
async def test_notification_orchestrator_escalation_pipeline():
    """NotificationOrchestrator triggers escalation for unacknowledged critical notifications."""
    import time

    orchestrator = NotificationOrchestrator(
        ack_manager=AcknowledgementManager(ack_timeout_seconds=0),
    )

    event = AgentDomainEvent(
        event_type="FireDetected",
        agent_name="VisionAgent",
        payload={"zone_id": "Zone-E", "confidence": "0.99"},
    )
    notifications, _ = await orchestrator.process_event(event, zone_id="Zone-E")
    assert len(notifications) == 1

    notif = notifications[0]
    # Force overdue by setting deadline in the past
    orchestrator.ack_manager._pending[notif.notification_id] = time.monotonic() - 1

    escalation_events = await orchestrator.process_escalation(
        notif,
        escalation_policy_id="escalation_emergency",
        trace_id=event.trace_id,
    )

    assert any(e.event_type == "NotificationEscalated" for e in escalation_events)
    assert len(notif.escalation_records) == 1
    assert notif.escalation_records[0].level == 1
