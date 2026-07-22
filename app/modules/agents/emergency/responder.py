"""responder.py — Responder Dispatch Coordinator."""

from app.modules.agents.emergency.models import ResourceAssignment


class ResponderCoordinator:
    """Dispatches and tracks active responder assignments."""

    @staticmethod
    def coordinate_dispatch(assignments: list[ResourceAssignment]) -> list[str]:
        """Format dispatch status summary."""
        return [f"Dispatched {a.resource_type} '{a.resource_id}' to {a.assigned_zone} (ETA: {a.eta_minutes}m)" for a in assignments]
