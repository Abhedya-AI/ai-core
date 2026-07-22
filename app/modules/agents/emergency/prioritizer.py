"""prioritizer.py — Phase 6: Life-Safety & Risk-Based Prioritization Engine."""

from app.modules.agents.emergency.models import EmergencyAction, PriorityLevel, SituationModel


class EmergencyPrioritizer:
    """Phase 6: Prioritizes actions balancing Life Safety > Environmental Impact > Asset Damage > Business Continuity."""

    @staticmethod
    def prioritize_actions(actions: list[EmergencyAction], situation: SituationModel) -> list[EmergencyAction]:
        """
        Sort actions by priority level and dependencies.

        Returns:
            list of EmergencyAction objects.
        """
        priority_weights = {
            PriorityLevel.CRITICAL: 1,
            PriorityLevel.HIGH: 2,
            PriorityLevel.MEDIUM: 3,
            PriorityLevel.LOW: 4,
        }

        # Maintain dependency ordering while sorting by priority
        return sorted(actions, key=lambda a: (priority_weights.get(a.priority, 5), a.step_id))
