"""planner.py — Phase 3: Dependency-Aware Emergency Action Planner."""

from app.modules.agents.emergency.models import EmergencyAction, PriorityLevel, SituationModel


class EmergencyPlanner:
    """Phase 3: Generates an ordered action sequence with explicit step dependencies and execution prerequisites."""

    @staticmethod
    def plan_emergency_response(situation: SituationModel) -> list[EmergencyAction]:
        """
        Generate ordered dependency-aware action sequence.

        Returns:
            list of EmergencyAction objects.
        """
        actions = [
            EmergencyAction(
                step_id=1,
                action_type="SHUT_VALVE",
                description="Isolate primary gas supply valve V-12 to stop leakage.",
                target_entity="VALVE-V12",
                priority=PriorityLevel.CRITICAL,
                dependencies=[],
                estimated_duration_min=1.0,
            ),
            EmergencyAction(
                step_id=2,
                action_type="TRIGGER_ALARM",
                description="Activate facility siren alarm and automated PA emergency broadcast.",
                target_entity=situation.zone_id,
                priority=PriorityLevel.CRITICAL,
                dependencies=[1],
                estimated_duration_min=0.5,
            ),
            EmergencyAction(
                step_id=3,
                action_type="EVACUATE",
                description=f"Evacuate {situation.occupants} occupants from {situation.zone_id} via accessible exits: {', '.join(situation.accessible_exits)}.",
                target_entity=situation.zone_id,
                priority=PriorityLevel.CRITICAL,
                dependencies=[2],
                estimated_duration_min=3.5,
            ),
            EmergencyAction(
                step_id=4,
                action_type="DISPATCH_TEAM",
                description=f"Dispatch Fire & Rescue Team Alpha to {situation.zone_id}.",
                target_entity="FIRE_TEAM_ALPHA",
                priority=PriorityLevel.HIGH,
                dependencies=[3],
                estimated_duration_min=2.0,
            ),
            EmergencyAction(
                step_id=5,
                action_type="NOTIFY_MEDICAL",
                description="Stage Medical Emergency Team at primary assembly point.",
                target_entity="MEDICAL_TEAM_1",
                priority=PriorityLevel.HIGH,
                dependencies=[4],
                estimated_duration_min=2.5,
            ),
            EmergencyAction(
                step_id=6,
                action_type="INSPECT_ADJACENT",
                description="Inspect adjacent zone corridors for hazardous gas accumulation.",
                target_entity="ZONE-C",
                priority=PriorityLevel.MEDIUM,
                dependencies=[5],
                estimated_duration_min=5.0,
            ),
        ]
        return actions
