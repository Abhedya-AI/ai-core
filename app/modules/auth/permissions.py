"""
app/modules/auth/permissions.py — Permission Codes Registry.

Every protected action in ABHEDYA is guarded by a permission code.
These codes are attached to roles in the RBAC table and evaluated
per-request by the PolicyEngine (ABAC).

Convention:  <resource>.<action>
"""

from enum import Enum


class Permission(str, Enum):
    """
    All permission codes in ABHEDYA.

    Roles grant sets of these permissions.
    Individual endpoints declare which permission they require.
    """

    # ── Incident Management ──────────────────────────────────────────────────
    INCIDENT_READ = "incident.read"
    INCIDENT_CREATE = "incident.create"
    INCIDENT_UPDATE = "incident.update"
    INCIDENT_CLOSE = "incident.close"
    INCIDENT_INVESTIGATE = "incident.investigate"

    # ── Risk Intelligence ────────────────────────────────────────────────────
    RISK_RUN = "risk.run"
    RISK_READ = "risk.read"

    # ── Prediction ───────────────────────────────────────────────────────────
    PREDICTION_RUN = "prediction.run"
    PREDICTION_READ = "prediction.read"

    # ── Compliance ───────────────────────────────────────────────────────────
    COMPLIANCE_CHECK = "compliance.check"
    COMPLIANCE_READ = "compliance.read"

    # ── Emergency ────────────────────────────────────────────────────────────
    EMERGENCY_ACTIVATE = "emergency.activate"
    EMERGENCY_READ = "emergency.read"
    EMERGENCY_CLOSE = "emergency.close"

    # ── Documents ────────────────────────────────────────────────────────────
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_READ = "document.read"
    DOCUMENT_DELETE = "document.delete"

    # ── Workflow / Supervisor ─────────────────────────────────────────────────
    WORKFLOW_EXECUTE = "workflow.execute"
    WORKFLOW_READ = "workflow.read"

    # ── Notifications ─────────────────────────────────────────────────────────
    NOTIFICATION_SEND = "notification.send"
    NOTIFICATION_READ = "notification.read"

    # ── Knowledge Graph ───────────────────────────────────────────────────────
    GRAPH_READ = "graph.read"
    GRAPH_WRITE = "graph.write"

    # ── Analytics ─────────────────────────────────────────────────────────────
    ANALYTICS_READ = "analytics.read"

    # ── Administration ────────────────────────────────────────────────────────
    ADMIN_USERS_READ = "admin.users.read"
    ADMIN_USERS_WRITE = "admin.users.write"
    ADMIN_ROLES_READ = "admin.roles.read"
    ADMIN_ROLES_WRITE = "admin.roles.write"
    ADMIN_AUDIT_READ = "admin.audit.read"
    ADMIN_SETTINGS = "admin.settings"


# ── Role → Permission Mapping (RBAC) ──────────────────────────────────────────

ROLE_PERMISSIONS: dict[str, list[Permission]] = {
    "SAFETY_OFFICER": [
        Permission.INCIDENT_READ,
        Permission.INCIDENT_CREATE,
        Permission.INCIDENT_UPDATE,
        Permission.INCIDENT_INVESTIGATE,
        Permission.RISK_RUN,
        Permission.RISK_READ,
        Permission.PREDICTION_RUN,
        Permission.PREDICTION_READ,
        Permission.COMPLIANCE_CHECK,
        Permission.COMPLIANCE_READ,
        Permission.EMERGENCY_ACTIVATE,
        Permission.EMERGENCY_READ,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPLOAD,
        Permission.WORKFLOW_EXECUTE,
        Permission.WORKFLOW_READ,
        Permission.NOTIFICATION_READ,
        Permission.NOTIFICATION_SEND,
        Permission.GRAPH_READ,
        Permission.ANALYTICS_READ,
    ],
    "PLANT_MANAGER": [
        Permission.INCIDENT_READ,
        Permission.INCIDENT_CREATE,
        Permission.INCIDENT_UPDATE,
        Permission.INCIDENT_CLOSE,
        Permission.INCIDENT_INVESTIGATE,
        Permission.RISK_RUN,
        Permission.RISK_READ,
        Permission.PREDICTION_RUN,
        Permission.PREDICTION_READ,
        Permission.COMPLIANCE_CHECK,
        Permission.COMPLIANCE_READ,
        Permission.EMERGENCY_ACTIVATE,
        Permission.EMERGENCY_READ,
        Permission.EMERGENCY_CLOSE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPLOAD,
        Permission.WORKFLOW_EXECUTE,
        Permission.WORKFLOW_READ,
        Permission.NOTIFICATION_READ,
        Permission.NOTIFICATION_SEND,
        Permission.GRAPH_READ,
        Permission.ANALYTICS_READ,
    ],
    "SHIFT_SUPERVISOR": [
        Permission.INCIDENT_READ,
        Permission.INCIDENT_CREATE,
        Permission.INCIDENT_UPDATE,
        Permission.RISK_READ,
        Permission.PREDICTION_READ,
        Permission.COMPLIANCE_READ,
        Permission.EMERGENCY_READ,
        Permission.DOCUMENT_READ,
        Permission.WORKFLOW_READ,
        Permission.NOTIFICATION_READ,
        Permission.GRAPH_READ,
        Permission.ANALYTICS_READ,
    ],
    "MAINTENANCE_TECHNICIAN": [
        Permission.INCIDENT_READ,
        Permission.INCIDENT_UPDATE,
        Permission.RISK_READ,
        Permission.COMPLIANCE_READ,
        Permission.DOCUMENT_READ,
        Permission.WORKFLOW_READ,
        Permission.NOTIFICATION_READ,
        Permission.GRAPH_READ,
    ],
    "AUDITOR": [
        Permission.INCIDENT_READ,
        Permission.RISK_READ,
        Permission.PREDICTION_READ,
        Permission.COMPLIANCE_READ,
        Permission.EMERGENCY_READ,
        Permission.DOCUMENT_READ,
        Permission.WORKFLOW_READ,
        Permission.NOTIFICATION_READ,
        Permission.GRAPH_READ,
        Permission.ANALYTICS_READ,
        Permission.ADMIN_AUDIT_READ,
    ],
    "CONTRACTOR": [
        Permission.INCIDENT_READ,
        Permission.RISK_READ,
        Permission.DOCUMENT_READ,
        Permission.NOTIFICATION_READ,
    ],
    "SYSTEM_ADMIN": [p for p in Permission],  # All permissions
    "AI_AGENT": [
        Permission.INCIDENT_READ,
        Permission.INCIDENT_CREATE,
        Permission.INCIDENT_UPDATE,
        Permission.RISK_RUN,
        Permission.RISK_READ,
        Permission.PREDICTION_RUN,
        Permission.PREDICTION_READ,
        Permission.COMPLIANCE_CHECK,
        Permission.COMPLIANCE_READ,
        Permission.EMERGENCY_READ,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPLOAD,
        Permission.WORKFLOW_EXECUTE,
        Permission.WORKFLOW_READ,
        Permission.NOTIFICATION_SEND,
        Permission.NOTIFICATION_READ,
        Permission.GRAPH_READ,
        Permission.GRAPH_WRITE,
        Permission.ANALYTICS_READ,
    ],
}


def get_permissions_for_roles(roles: list[str]) -> set[Permission]:
    """Resolve the union of all permissions for a list of role names."""
    perms: set[Permission] = set()
    for role in roles:
        perms.update(ROLE_PERMISSIONS.get(role, []))
    return perms
