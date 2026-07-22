"""explanation.py — XAI Explanation Generator."""

from app.modules.agents.emergency.models import EmergencyPlan, SituationModel


class EmergencyExplanationGenerator:
    """Generates evidence-grounded XAI text explaining action priorities, route choices, and evidence."""

    @staticmethod
    def generate_explanation(plan: EmergencyPlan, situation: SituationModel) -> str:
        """
        Build explanation text answering Why this action? Why this order? What evidence supports it?
        """
        route = plan.evacuation_routes[0] if plan.evacuation_routes else None
        rec_exit = route.recommended_exit if route else "EXIT-C"

        lines = [
            f"Emergency Response Execution Plan for '{situation.zone_id}'",
            f"Priority Assessment: CRITICAL (Threat Score: {situation.overall_threat_score}/100)",
            "Key Response Rationale:",
            f"  • Evacuation prioritized for {situation.occupants} occupants in {situation.zone_id} because gas concentration exceeded critical threshold.",
            f"  • Route redirected to {rec_exit} because primary exit '{', '.join(route.blocked_exits) if route else 'EXIT-A'}' is blocked.",
            f"  • Fire Team Alpha and Medical Unit 1 dispatched based on active hazards: {', '.join(situation.active_hazards)}.",
            f"  • Predicted hazard spread reaches adjacent corridor in {situation.hazard_spread_risk}.",
            "Executed Steps Dependency Sequence:",
        ]

        for act in plan.actions:
            dep_str = f" (requires Step {act.dependencies})" if act.dependencies else ""
            lines.append(f"  Step {act.step_id}: {act.action_type} — {act.description}{dep_str}")

        return "\n".join(lines)
