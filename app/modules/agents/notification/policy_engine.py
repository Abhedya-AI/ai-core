"""policy_engine.py — Configuration-driven Policy Engine.

Evaluates domain events and determines:
  - Whether a notification should be sent.
  - Severity classification.
  - Required channels.
  - Whether acknowledgement is required.
  - Escalation policy reference.
"""

from app.core.logging import get_logger
from app.modules.agents.notification.models import NotificationChannel, NotificationSeverity

log = get_logger("agents.notification.policy_engine")

# ---------------------------------------------------------------------------
# Policy Configuration  (configuration-driven — no agent names embedded)
# ---------------------------------------------------------------------------

# Maps event_type → (severity, channels, requires_ack)
_EVENT_POLICIES: dict[str, tuple[NotificationSeverity, list[NotificationChannel], bool]] = {
    # Critical / Emergency
    "FireDetected": (
        NotificationSeverity.EMERGENCY,
        [NotificationChannel.SMS, NotificationChannel.VOICE, NotificationChannel.PUSH,
         NotificationChannel.SLACK, NotificationChannel.PAGERDUTY, NotificationChannel.DASHBOARD],
        True,
    ),
    "SmokeDetected": (
        NotificationSeverity.CRITICAL,
        [NotificationChannel.SMS, NotificationChannel.PUSH,
         NotificationChannel.SLACK, NotificationChannel.DASHBOARD],
        True,
    ),
    "EmergencyPlanGenerated": (
        NotificationSeverity.EMERGENCY,
        [NotificationChannel.SMS, NotificationChannel.VOICE, NotificationChannel.PUSH,
         NotificationChannel.TEAMS, NotificationChannel.PAGERDUTY, NotificationChannel.DASHBOARD],
        True,
    ),
    "EvacuationInitiated": (
        NotificationSeverity.EMERGENCY,
        [NotificationChannel.SMS, NotificationChannel.VOICE, NotificationChannel.PUSH,
         NotificationChannel.DASHBOARD, NotificationChannel.PAGERDUTY],
        True,
    ),
    "HighRiskDetected": (
        NotificationSeverity.HIGH,
        [NotificationChannel.SMS, NotificationChannel.PUSH,
         NotificationChannel.SLACK, NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
        True,
    ),
    "RiskDetected": (
        NotificationSeverity.MEDIUM,
        [NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.DASHBOARD],
        False,
    ),
    "IncidentPredicted": (
        NotificationSeverity.HIGH,
        [NotificationChannel.EMAIL, NotificationChannel.PUSH,
         NotificationChannel.SLACK, NotificationChannel.DASHBOARD],
        True,
    ),
    "EquipmentFailurePredicted": (
        NotificationSeverity.HIGH,
        [NotificationChannel.EMAIL, NotificationChannel.TEAMS,
         NotificationChannel.PUSH, NotificationChannel.DASHBOARD],
        False,
    ),
    "MaintenanceForecast": (
        NotificationSeverity.MEDIUM,
        [NotificationChannel.EMAIL, NotificationChannel.TEAMS, NotificationChannel.DASHBOARD],
        False,
    ),
    "RootCauseIdentified": (
        NotificationSeverity.MEDIUM,
        [NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.DASHBOARD],
        False,
    ),
    "ComplianceViolationDetected": (
        NotificationSeverity.HIGH,
        [NotificationChannel.EMAIL, NotificationChannel.TEAMS,
         NotificationChannel.PUSH, NotificationChannel.DASHBOARD],
        True,
    ),
    "PermitExpired": (
        NotificationSeverity.HIGH,
        [NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.DASHBOARD],
        False,
    ),
    "ResourceAllocated": (
        NotificationSeverity.MEDIUM,
        [NotificationChannel.PUSH, NotificationChannel.SLACK, NotificationChannel.DASHBOARD],
        False,
    ),
    "ResponderDispatched": (
        NotificationSeverity.HIGH,
        [NotificationChannel.SMS, NotificationChannel.PUSH, NotificationChannel.DASHBOARD],
        True,
    ),
    "DocumentIndexed": (
        NotificationSeverity.INFORMATIONAL,
        [NotificationChannel.DASHBOARD],
        False,
    ),
    "PPEViolationDetected": (
        NotificationSeverity.MEDIUM,
        [NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.DASHBOARD],
        False,
    ),
    "ZoneOccupancyExceeded": (
        NotificationSeverity.MEDIUM,
        [NotificationChannel.PUSH, NotificationChannel.DASHBOARD],
        False,
    ),
    "SpillDetected": (
        NotificationSeverity.CRITICAL,
        [NotificationChannel.SMS, NotificationChannel.PUSH,
         NotificationChannel.SLACK, NotificationChannel.DASHBOARD],
        True,
    ),
    "WORKER_STATUS_UPDATED": (
        NotificationSeverity.LOW,
        [NotificationChannel.DASHBOARD],
        False,
    ),
}

_DEFAULT_POLICY: tuple[NotificationSeverity, list[NotificationChannel], bool] = (
    NotificationSeverity.LOW,
    [NotificationChannel.DASHBOARD],
    False,
)


class PolicyEvaluationResult:
    """Result of a policy evaluation for a given domain event."""

    def __init__(
        self,
        should_notify: bool,
        severity: NotificationSeverity,
        channels: list[NotificationChannel],
        requires_acknowledgement: bool,
        escalation_policy_id: str,
    ) -> None:
        self.should_notify = should_notify
        self.severity = severity
        self.channels = channels
        self.requires_acknowledgement = requires_acknowledgement
        self.escalation_policy_id = escalation_policy_id


class PolicyEngine:
    """
    Evaluates domain events against the notification policy registry.

    All policy configuration lives in _EVENT_POLICIES — no code change
    is required to add a new event type mapping.
    """

    def evaluate(self, event_type: str, payload: dict) -> PolicyEvaluationResult:
        """
        Determine notification policy for a domain event.

        Args:
            event_type: Canonical domain event type string.
            payload: Event payload (used for severity overrides when available).

        Returns:
            PolicyEvaluationResult with channels, severity, and ack requirements.
        """
        # Severity override from payload if richer context exists
        policy_severity, channels, requires_ack = _EVENT_POLICIES.get(event_type, _DEFAULT_POLICY)

        # Honor explicit severity from payload when present
        payload_severity = payload.get("severity", "")
        if payload_severity == "CRITICAL" and policy_severity.value not in ("EMERGENCY",):
            policy_severity = NotificationSeverity.CRITICAL
            requires_ack = True
        elif payload_severity == "HIGH" and policy_severity.value == "LOW":
            policy_severity = NotificationSeverity.HIGH

        # Informational events: do not require ack
        if policy_severity == NotificationSeverity.INFORMATIONAL:
            requires_ack = False

        # Derive escalation policy ID from severity
        escalation_policy_id = f"escalation_{policy_severity.value.lower()}"

        log.debug(
            f"PolicyEngine: event_type={event_type} → severity={policy_severity.value}, "
            f"channels={[c.value for c in channels]}, ack={requires_ack}"
        )

        return PolicyEvaluationResult(
            should_notify=True,
            severity=policy_severity,
            channels=channels,
            requires_acknowledgement=requires_ack,
            escalation_policy_id=escalation_policy_id,
        )
