"""recommendation.py — Phase 8: Categorized Emergency Action Recommendation Engine."""

from app.modules.agents.emergency.models import EmergencyPlan, SituationModel


class EmergencyRecommendationEngine:
    """Phase 8: Categorizes emergency response actions by operational phase (Immediate 0-5m, Short-Term 5-30m, Recovery)."""

    @staticmethod
    def generate_recommendations(plan: EmergencyPlan, situation: SituationModel) -> tuple[list[str], dict[str, list[str]]]:
        """
        Generate categorized actions.

        Returns:
            tuple[flattened_list, categorized_dict]
        """
        immediate = [
            f"Evacuate {situation.zone_id} immediately via exit: {plan.evacuation_routes[0].recommended_exit if plan.evacuation_routes else 'EXIT-C'}.",
            "Isolate gas supply valve V-12 immediately.",
            "Activate facility siren alarm and automated PA emergency broadcast.",
            "Dispatch Fire & Rescue Team Alpha and Medical Unit 1.",
        ]

        short_term = [
            "Inspect adjacent Zone C corridors for hazardous gas accumulation.",
            "Confirm personnel headcount at primary evacuation assembly point.",
            "Deploy backup emergency ventilation system.",
        ]

        recovery = [
            "Begin structural integrity and gas leak damage assessment.",
            "Restore plant power utilities under supervisor sign-off.",
            "Prepare official regulatory incident investigation report.",
        ]

        categorized = {
            "Immediate (0-5 min)": immediate,
            "Short-Term (5-30 min)": short_term,
            "Recovery": recovery,
        }

        flattened = immediate + short_term + recovery
        return flattened, categorized
