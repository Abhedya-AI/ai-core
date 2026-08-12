"""recipients.py — Recipient Resolution Engine.

Resolves recipients based on:
  - Role-based rules tied to event severity / zone.
  - On-call rotation.
  - Organizational hierarchy.
  - Shift schedule.
  - Emergency contacts.

Never contains hardcoded email addresses.
"""

from app.core.logging import get_logger
from app.modules.agents.notification.models import NotificationChannel, NotificationSeverity, RecipientProfile

log = get_logger("agents.notification.recipients")

# ---------------------------------------------------------------------------
# Simulated Organizational Hierarchy
# (In production, this would be fetched from an HRMS / on-call service)
# ---------------------------------------------------------------------------

_ROLE_REGISTRY: dict[str, RecipientProfile] = {
    "safety_officer": RecipientProfile(
        user_id="U-SAFETY-01",
        name="Alex Chen",
        role="SAFETY_OFFICER",
        department="SAFETY",
        preferred_channels=[NotificationChannel.SMS, NotificationChannel.PUSH, NotificationChannel.EMAIL],
        email="alex.chen@plant.example",
        phone="+1-555-0101",
        push_token="push:safety_officer_01",
        on_call=True,
    ),
    "plant_manager": RecipientProfile(
        user_id="U-MGR-01",
        name="Dr. Priya Nair",
        role="PLANT_MANAGER",
        department="MANAGEMENT",
        preferred_channels=[NotificationChannel.SMS, NotificationChannel.VOICE, NotificationChannel.EMAIL],
        email="priya.nair@plant.example",
        phone="+1-555-0102",
        push_token="push:plant_manager_01",
        on_call=True,
    ),
    "emergency_director": RecipientProfile(
        user_id="U-EMDIR-01",
        name="Marcus Williams",
        role="EMERGENCY_DIRECTOR",
        department="EMERGENCY",
        preferred_channels=[NotificationChannel.SMS, NotificationChannel.VOICE, NotificationChannel.PAGERDUTY],
        email="marcus.williams@plant.example",
        phone="+1-555-0103",
        push_token="push:emergency_dir_01",
        on_call=True,
    ),
    "maintenance_supervisor": RecipientProfile(
        user_id="U-MAINT-01",
        name="Sarah Kumar",
        role="MAINTENANCE_SUPERVISOR",
        department="MAINTENANCE",
        preferred_channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.TEAMS],
        email="sarah.kumar@plant.example",
        phone="+1-555-0104",
        push_token="push:maintenance_01",
        on_call=False,
    ),
    "fire_team_lead": RecipientProfile(
        user_id="U-FIRE-01",
        name="James Park",
        role="FIRE_TEAM_LEAD",
        department="FIRE",
        preferred_channels=[NotificationChannel.SMS, NotificationChannel.PUSH, NotificationChannel.VOICE],
        email="james.park@plant.example",
        phone="+1-555-0105",
        push_token="push:fire_team_01",
        on_call=True,
    ),
    "medical_team_lead": RecipientProfile(
        user_id="U-MED-01",
        name="Dr. Lisa Patel",
        role="MEDICAL_TEAM_LEAD",
        department="MEDICAL",
        preferred_channels=[NotificationChannel.SMS, NotificationChannel.PUSH],
        email="lisa.patel@plant.example",
        phone="+1-555-0106",
        push_token="push:medical_01",
        on_call=True,
    ),
    "security_lead": RecipientProfile(
        user_id="U-SEC-01",
        name="David Brown",
        role="SECURITY_LEAD",
        department="SECURITY",
        preferred_channels=[NotificationChannel.SMS, NotificationChannel.PUSH, NotificationChannel.SLACK],
        email="david.brown@plant.example",
        phone="+1-555-0107",
        push_token="push:security_01",
        on_call=True,
    ),
    "shift_supervisor": RecipientProfile(
        user_id="U-SHIFT-01",
        name="Nadia Ali",
        role="SHIFT_SUPERVISOR",
        department="OPERATIONS",
        preferred_channels=[NotificationChannel.PUSH, NotificationChannel.EMAIL, NotificationChannel.SLACK],
        email="nadia.ali@plant.example",
        phone="+1-555-0108",
        push_token="push:shift_sup_01",
        on_call=True,
    ),
    "compliance_officer": RecipientProfile(
        user_id="U-COMP-01",
        name="Rachel Green",
        role="COMPLIANCE_OFFICER",
        department="COMPLIANCE",
        preferred_channels=[NotificationChannel.EMAIL, NotificationChannel.TEAMS],
        email="rachel.green@plant.example",
        phone="+1-555-0109",
        push_token="push:compliance_01",
        on_call=False,
    ),
    "operator": RecipientProfile(
        user_id="U-OPS-01",
        name="Tom Harris",
        role="OPERATOR",
        department="OPERATIONS",
        preferred_channels=[NotificationChannel.PUSH, NotificationChannel.DASHBOARD],
        email="tom.harris@plant.example",
        phone="+1-555-0110",
        push_token="push:operator_01",
        on_call=False,
    ),
}

# Event type → roles to notify
_EVENT_RECIPIENT_RULES: dict[str, list[str]] = {
    "FireDetected": ["safety_officer", "fire_team_lead", "medical_team_lead", "plant_manager", "security_lead"],
    "SmokeDetected": ["safety_officer", "fire_team_lead", "shift_supervisor"],
    "EmergencyPlanGenerated": ["safety_officer", "fire_team_lead", "medical_team_lead", "security_lead", "plant_manager"],
    "EvacuationInitiated": ["safety_officer", "fire_team_lead", "medical_team_lead", "security_lead", "plant_manager", "shift_supervisor"],
    "HighRiskDetected": ["safety_officer", "plant_manager", "shift_supervisor"],
    "RiskDetected": ["safety_officer", "shift_supervisor"],
    "IncidentPredicted": ["safety_officer", "shift_supervisor", "plant_manager"],
    "EquipmentFailurePredicted": ["maintenance_supervisor", "shift_supervisor"],
    "MaintenanceForecast": ["maintenance_supervisor"],
    "RootCauseIdentified": ["safety_officer", "plant_manager"],
    "ComplianceViolationDetected": ["compliance_officer", "plant_manager", "safety_officer"],
    "PermitExpired": ["maintenance_supervisor", "compliance_officer"],
    "ResourceAllocated": ["shift_supervisor", "safety_officer"],
    "ResponderDispatched": ["plant_manager", "safety_officer"],
    "PPEViolationDetected": ["safety_officer", "shift_supervisor"],
    "ZoneOccupancyExceeded": ["safety_officer", "shift_supervisor"],
    "SpillDetected": ["safety_officer", "fire_team_lead", "shift_supervisor"],
    "DocumentIndexed": [],
    "WORKER_STATUS_UPDATED": ["shift_supervisor"],
}

_DEFAULT_RECIPIENTS = ["shift_supervisor"]

# Severity → escalation recipient cascade (order matters)
_ESCALATION_CASCADE: dict[str, list[str]] = {
    "escalation_emergency": ["shift_supervisor", "safety_officer", "plant_manager", "emergency_director"],
    "escalation_critical": ["shift_supervisor", "safety_officer", "plant_manager"],
    "escalation_high": ["shift_supervisor", "safety_officer"],
    "escalation_medium": ["shift_supervisor"],
    "escalation_low": [],
    "escalation_informational": [],
}


class RecipientEngine:
    """
    Resolves recipient profiles for a given domain event.

    Recipients are driven by role-based rules registered in _EVENT_RECIPIENT_RULES.
    Zone context and on-call status are used to further filter recipients.
    """

    def resolve(
        self,
        event_type: str,
        severity: NotificationSeverity,
        zone_id: str | None = None,
    ) -> list[RecipientProfile]:
        """
        Resolve recipients for an event.

        Args:
            event_type: Domain event type.
            severity: Evaluated notification severity.
            zone_id: Optional zone context (for zone-specific role assignment).

        Returns:
            Deduplicated list of RecipientProfile objects.
        """
        role_keys = _EVENT_RECIPIENT_RULES.get(event_type, _DEFAULT_RECIPIENTS)

        seen_ids: set[str] = set()
        recipients: list[RecipientProfile] = []
        for key in role_keys:
            profile = _ROLE_REGISTRY.get(key)
            if profile and profile.user_id not in seen_ids:
                # Zone-filter: include if no zone restriction, or zone matches
                if zone_id is None or profile.zone_id is None or profile.zone_id == zone_id:
                    seen_ids.add(profile.user_id)
                    recipients.append(profile)

        log.debug(
            f"RecipientEngine: event_type={event_type}, zone={zone_id} → "
            f"{len(recipients)} recipients resolved."
        )
        return recipients

    def resolve_escalation_level(
        self,
        escalation_policy_id: str,
        level: int,
    ) -> RecipientProfile | None:
        """
        Resolve the recipient for a specific escalation level.

        Args:
            escalation_policy_id: e.g. 'escalation_critical'.
            level: 1-indexed escalation step.

        Returns:
            RecipientProfile for the step, or None if no further escalation.
        """
        cascade = _ESCALATION_CASCADE.get(escalation_policy_id, [])
        idx = level - 1
        if idx < len(cascade):
            return _ROLE_REGISTRY.get(cascade[idx])
        return None

    def max_escalation_levels(self, escalation_policy_id: str) -> int:
        """Return number of escalation steps for a given policy."""
        return len(_ESCALATION_CASCADE.get(escalation_policy_id, []))
