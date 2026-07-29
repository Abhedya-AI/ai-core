"""escalation.py — Escalation Engine.

Implements time-based, role-based, severity-based, and acknowledgement-based
escalation policies.

Example escalation cascade:
  t=0m  → Shift Supervisor (SMS + Push)
  t=5m  → Safety Officer (SMS + Voice)
  t=10m → Plant Manager (SMS + Voice + PagerDuty)
  t=15m → Emergency Director (all channels)
"""

from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.agents.notification.models import EscalationRecord, NotificationChannel

log = get_logger("agents.notification.escalation")

# Time between escalation levels (seconds)
_ESCALATION_INTERVAL_SECONDS: dict[str, int] = {
    "escalation_emergency": 60,    # 1 min between levels
    "escalation_critical": 180,    # 3 min between levels
    "escalation_high": 300,        # 5 min between levels
    "escalation_medium": 600,      # 10 min between levels
    "escalation_low": 0,           # no escalation
    "escalation_informational": 0, # no escalation
}

# Extra channels to add at each escalation level
_ESCALATION_CHANNEL_ESCALATION: dict[str, list[list[NotificationChannel]]] = {
    "escalation_emergency": [
        [NotificationChannel.SMS, NotificationChannel.PUSH],
        [NotificationChannel.VOICE, NotificationChannel.PAGERDUTY],
        [NotificationChannel.VOICE, NotificationChannel.PAGERDUTY, NotificationChannel.TEAMS],
        [NotificationChannel.VOICE, NotificationChannel.PAGERDUTY, NotificationChannel.TEAMS, NotificationChannel.WEBHOOK],
    ],
    "escalation_critical": [
        [NotificationChannel.SMS, NotificationChannel.PUSH],
        [NotificationChannel.VOICE, NotificationChannel.SLACK],
        [NotificationChannel.PAGERDUTY, NotificationChannel.TEAMS],
    ],
    "escalation_high": [
        [NotificationChannel.EMAIL, NotificationChannel.PUSH],
        [NotificationChannel.SMS, NotificationChannel.SLACK],
    ],
    "escalation_medium": [
        [NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
    ],
}


class EscalationEngine:
    """
    Manages multi-level escalation for unacknowledged critical notifications.

    Escalation is triggered by the orchestrator when the acknowledgement
    manager reports an overdue notification.
    """

    def __init__(self) -> None:
        # notification_id → current escalation level (1-indexed)
        self._escalation_levels: dict[str, int] = {}
        # notification_id → list of EscalationRecord
        self._escalation_records: dict[str, list[EscalationRecord]] = {}

    def needs_escalation(
        self,
        notification_id: str,
        escalation_policy_id: str,
    ) -> bool:
        """Return True if this notification has not yet been fully escalated."""
        if escalation_policy_id in ("escalation_low", "escalation_informational"):
            return False
        current_level = self._escalation_levels.get(notification_id, 0)
        max_levels = len(_ESCALATION_CHANNEL_ESCALATION.get(escalation_policy_id, []))
        return current_level < max_levels

    def escalate(
        self,
        notification_id: str,
        escalation_policy_id: str,
        escalated_to: str,
    ) -> tuple[EscalationRecord, list[NotificationChannel]]:
        """
        Advance escalation by one level.

        Args:
            notification_id: ID of the unacknowledged notification.
            escalation_policy_id: Policy identifier.
            escalated_to: User ID or role name being escalated to.

        Returns:
            Tuple of (EscalationRecord, channels to use for escalation message).
        """
        current_level = self._escalation_levels.get(notification_id, 0)
        new_level = current_level + 1

        channels_for_level = _ESCALATION_CHANNEL_ESCALATION.get(
            escalation_policy_id, []
        )
        idx = current_level  # 0-indexed access
        channels = channels_for_level[idx] if idx < len(channels_for_level) else [NotificationChannel.SMS]

        record = EscalationRecord(
            notification_id=notification_id,
            level=new_level,
            escalated_to=escalated_to,
            triggered_at=datetime.now(timezone.utc).isoformat(),
            reason="NO_ACKNOWLEDGEMENT",
        )

        self._escalation_levels[notification_id] = new_level
        if notification_id not in self._escalation_records:
            self._escalation_records[notification_id] = []
        self._escalation_records[notification_id].append(record)

        log.warning(
            f"EscalationEngine: notification={notification_id} escalated to level={new_level}, "
            f"recipient='{escalated_to}', channels={[c.value for c in channels]}"
        )
        return record, channels

    def get_escalation_interval(self, escalation_policy_id: str) -> int:
        """Return seconds between escalation levels for a policy."""
        return _ESCALATION_INTERVAL_SECONDS.get(escalation_policy_id, 300)

    def get_records(self, notification_id: str) -> list[EscalationRecord]:
        """Return all escalation records for a notification."""
        return self._escalation_records.get(notification_id, [])

    def current_level(self, notification_id: str) -> int:
        """Return the current escalation level (0 = not yet escalated)."""
        return self._escalation_levels.get(notification_id, 0)
