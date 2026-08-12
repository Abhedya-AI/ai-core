"""templates.py — Template Registry for Notification Agent.

Stores notification templates for all domain event types.
Templates support HTML, Markdown, plain text, and rich card formats.
"""

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.modules.agents.notification.models import NotificationChannel

log = get_logger("agents.notification.templates")


@dataclass
class NotificationTemplate:
    """A notification template with multi-format support."""

    template_id: str
    event_type: str
    version: str = "1.0"
    subject_template: str = ""
    body_text_template: str = ""
    body_html_template: str = ""
    body_markdown_template: str = ""
    rich_card_template: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Template Registry
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, NotificationTemplate] = {
    "FireDetected": NotificationTemplate(
        template_id="tpl_fire_detected",
        event_type="FireDetected",
        version="1.0",
        subject_template="🔥 FIRE DETECTED — Zone {{zone}} | Immediate Action Required",
        body_text_template=(
            "FIRE ALERT\n"
            "Zone: {{zone}}\n"
            "Confidence: {{confidence}}\n"
            "Detected At: {{timestamp}}\n"
            "Affected Assets: {{assets}}\n\n"
            "IMMEDIATE ACTIONS:\n{{actions}}\n\n"
            "ABHEDYA Safety Intelligence — Incident ID: {{incident_id}}"
        ),
        body_html_template=(
            "<h1>🔥 Fire Detected</h1>"
            "<table><tr><th>Zone</th><td>{{zone}}</td></tr>"
            "<tr><th>Confidence</th><td>{{confidence}}</td></tr>"
            "<tr><th>Detected At</th><td>{{timestamp}}</td></tr>"
            "<tr><th>Affected Assets</th><td>{{assets}}</td></tr></table>"
            "<h2>Immediate Actions</h2><ul>{{actions_html}}</ul>"
            "<p><em>ABHEDYA Safety Intelligence — Incident ID: {{incident_id}}</em></p>"
        ),
        body_markdown_template=(
            "# 🔥 Fire Detected\n\n"
            "| Field | Value |\n|---|---|\n"
            "| Zone | {{zone}} |\n"
            "| Confidence | {{confidence}} |\n"
            "| Detected At | {{timestamp}} |\n"
            "| Affected Assets | {{assets}} |\n\n"
            "## Immediate Actions\n{{actions}}\n\n"
            "*ABHEDYA Safety Intelligence — Incident ID: {{incident_id}}*"
        ),
    ),
    "SmokeDetected": NotificationTemplate(
        template_id="tpl_smoke_detected",
        event_type="SmokeDetected",
        version="1.0",
        subject_template="⚠️ SMOKE DETECTED — Zone {{zone}}",
        body_text_template=(
            "SMOKE ALERT\n"
            "Zone: {{zone}}\n"
            "Confidence: {{confidence}}\n"
            "Detected At: {{timestamp}}\n\n"
            "REQUIRED ACTIONS:\n{{actions}}\n\n"
            "Incident ID: {{incident_id}}"
        ),
        body_html_template=(
            "<h1>⚠️ Smoke Detected</h1>"
            "<p>Zone: <strong>{{zone}}</strong> | Confidence: {{confidence}}</p>"
            "<h2>Required Actions</h2><ul>{{actions_html}}</ul>"
        ),
        body_markdown_template=(
            "# ⚠️ Smoke Detected\n\n"
            "**Zone:** {{zone}} | **Confidence:** {{confidence}}\n\n"
            "## Required Actions\n{{actions}}\n\n*Incident ID: {{incident_id}}*"
        ),
    ),
    "EmergencyPlanGenerated": NotificationTemplate(
        template_id="tpl_emergency_plan",
        event_type="EmergencyPlanGenerated",
        version="1.0",
        subject_template="🚨 EMERGENCY PLAN ACTIVATED — Zone {{zone}} | Plan {{plan_id}}",
        body_text_template=(
            "EMERGENCY RESPONSE PLAN\n"
            "Plan ID: {{plan_id}}\n"
            "Zone: {{zone}}\n"
            "Actions: {{action_count}} steps\n"
            "Timestamp: {{timestamp}}\n\n"
            "EXECUTION PLAN:\n{{actions}}\n\n"
            "Incident ID: {{incident_id}}"
        ),
        body_html_template=(
            "<h1>🚨 Emergency Plan Activated</h1>"
            "<p>Plan: <strong>{{plan_id}}</strong> | Zone: <strong>{{zone}}</strong></p>"
            "<h2>Execution Steps</h2><ul>{{actions_html}}</ul>"
        ),
        body_markdown_template=(
            "# 🚨 Emergency Plan Activated\n\n"
            "**Plan ID:** {{plan_id}} | **Zone:** {{zone}}\n\n"
            "## Execution Steps\n{{actions}}\n\n*Incident ID: {{incident_id}}*"
        ),
    ),
    "HighRiskDetected": NotificationTemplate(
        template_id="tpl_high_risk",
        event_type="HighRiskDetected",
        version="1.0",
        subject_template="🔴 HIGH RISK DETECTED — Zone {{zone}} | Score {{risk_score}}",
        body_text_template=(
            "HIGH RISK ALERT\n"
            "Risk Score: {{risk_score}}\n"
            "Zone: {{zone}}\n"
            "Affected Workers: {{workers}}\n"
            "Recommendation: {{recommendation}}\n"
            "Timestamp: {{timestamp}}\n\n"
            "Incident ID: {{incident_id}}"
        ),
        body_html_template=(
            "<h1>🔴 High Risk Detected</h1>"
            "<table><tr><th>Risk Score</th><td>{{risk_score}}</td></tr>"
            "<tr><th>Zone</th><td>{{zone}}</td></tr>"
            "<tr><th>Affected Workers</th><td>{{workers}}</td></tr>"
            "<tr><th>Recommendation</th><td>{{recommendation}}</td></tr></table>"
        ),
        body_markdown_template=(
            "# 🔴 High Risk Detected\n\n"
            "| Field | Value |\n|---|---|\n"
            "| Risk Score | {{risk_score}} |\n"
            "| Zone | {{zone}} |\n"
            "| Affected Workers | {{workers}} |\n"
            "| Recommendation | {{recommendation}} |\n\n"
            "*Incident ID: {{incident_id}}*"
        ),
    ),
    "RiskDetected": NotificationTemplate(
        template_id="tpl_risk_detected",
        event_type="RiskDetected",
        version="1.0",
        subject_template="Risk Detected — Zone {{zone}}",
        body_text_template=(
            "Risk Alert\nZone: {{zone}}\nRisk Score: {{risk_score}}\n"
            "Recommendation: {{recommendation}}\nTimestamp: {{timestamp}}"
        ),
        body_html_template=(
            "<h2>Risk Detected</h2><p>Zone: {{zone}} | Score: {{risk_score}}</p>"
            "<p>{{recommendation}}</p>"
        ),
        body_markdown_template=(
            "## Risk Detected\n\n**Zone:** {{zone}} | **Score:** {{risk_score}}\n\n{{recommendation}}"
        ),
    ),
    "ComplianceViolationDetected": NotificationTemplate(
        template_id="tpl_compliance_violation",
        event_type="ComplianceViolationDetected",
        version="1.0",
        subject_template="⚖️ Compliance Violation — {{regulation}}",
        body_text_template=(
            "COMPLIANCE VIOLATION\n"
            "Regulation: {{regulation}}\n"
            "Violation: {{violation}}\n"
            "Zone: {{zone}}\n"
            "Severity: {{severity}}\n"
            "Timestamp: {{timestamp}}\n\n"
            "Incident ID: {{incident_id}}"
        ),
        body_html_template=(
            "<h1>⚖️ Compliance Violation</h1>"
            "<p>Regulation: <strong>{{regulation}}</strong></p>"
            "<p>Violation: {{violation}}</p>"
            "<p>Zone: {{zone}} | Severity: {{severity}}</p>"
        ),
        body_markdown_template=(
            "# ⚖️ Compliance Violation\n\n"
            "**Regulation:** {{regulation}}\n\n"
            "**Violation:** {{violation}}\n\n"
            "**Zone:** {{zone}} | **Severity:** {{severity}}\n\n"
            "*Incident ID: {{incident_id}}*"
        ),
    ),
    "EquipmentFailurePredicted": NotificationTemplate(
        template_id="tpl_equipment_failure",
        event_type="EquipmentFailurePredicted",
        version="1.0",
        subject_template="🔧 Equipment Failure Predicted — {{asset}}",
        body_text_template=(
            "PREDICTIVE MAINTENANCE ALERT\n"
            "Asset: {{asset}}\n"
            "Failure Probability: {{probability}}\n"
            "Time Horizon: {{horizon}}\n"
            "Recommended Action: {{recommendation}}\n"
            "Timestamp: {{timestamp}}"
        ),
        body_html_template=(
            "<h2>🔧 Equipment Failure Predicted</h2>"
            "<p>Asset: <strong>{{asset}}</strong></p>"
            "<p>Failure Probability: {{probability}} | Horizon: {{horizon}}</p>"
            "<p>Recommendation: {{recommendation}}</p>"
        ),
        body_markdown_template=(
            "## 🔧 Equipment Failure Predicted\n\n"
            "**Asset:** {{asset}} | **Probability:** {{probability}} | **Horizon:** {{horizon}}\n\n"
            "**Recommendation:** {{recommendation}}"
        ),
    ),
    "PermitExpired": NotificationTemplate(
        template_id="tpl_permit_expired",
        event_type="PermitExpired",
        version="1.0",
        subject_template="📋 Permit Expired — {{permit_id}}",
        body_text_template=(
            "PERMIT EXPIRY NOTICE\n"
            "Permit ID: {{permit_id}}\n"
            "Zone: {{zone}}\n"
            "Expired At: {{timestamp}}\n"
            "Action Required: Renew permit before resuming operations."
        ),
        body_html_template=(
            "<h2>📋 Permit Expired</h2>"
            "<p>Permit: <strong>{{permit_id}}</strong> | Zone: {{zone}}</p>"
            "<p>Action: Renew permit before resuming operations.</p>"
        ),
        body_markdown_template=(
            "## 📋 Permit Expired\n\n"
            "**Permit ID:** {{permit_id}} | **Zone:** {{zone}}\n\n"
            "**Action:** Renew permit before resuming operations."
        ),
    ),
    "_default": NotificationTemplate(
        template_id="tpl_default",
        event_type="_default",
        version="1.0",
        subject_template="ABHEDYA Alert — {{event_type}}",
        body_text_template=(
            "ABHEDYA Safety Intelligence Alert\n"
            "Event: {{event_type}}\n"
            "Timestamp: {{timestamp}}\n"
            "Details: {{details}}"
        ),
        body_html_template=(
            "<h2>ABHEDYA Alert</h2>"
            "<p>Event: <strong>{{event_type}}</strong></p>"
            "<p>Timestamp: {{timestamp}}</p>"
            "<p>{{details}}</p>"
        ),
        body_markdown_template=(
            "## ABHEDYA Alert\n\n"
            "**Event:** {{event_type}}\n\n{{details}}"
        ),
    ),
}


class TemplateRegistry:
    """
    Provides template lookup for all domain event types.
    Falls back to _default template when no specific template exists.
    """

    def get_template(self, event_type: str) -> NotificationTemplate:
        """Lookup the template for a given event type."""
        template = _TEMPLATES.get(event_type, _TEMPLATES["_default"])
        log.debug(f"TemplateRegistry: resolved template '{template.template_id}' for event '{event_type}'")
        return template

    def list_supported_events(self) -> list[str]:
        """Return all event types with registered templates."""
        return [k for k in _TEMPLATES if k != "_default"]
