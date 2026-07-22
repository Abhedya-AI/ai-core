"""evacuation.py — Phase 4: Evacuation Planning Engine."""

from app.modules.agents.emergency.models import EvacuationRoute, SituationModel
from app.modules.agents.emergency.routing import HazardAwareRouter


class EvacuationPlanner:
    """Phase 4: Leverages Knowledge Graph and HazardAwareRouter to compute safe evacuation routes."""

    @staticmethod
    def plan_evacuation(situation: SituationModel, blocked_exits: list[str]) -> list[EvacuationRoute]:
        """
        Build EvacuationRoute objects for affected zones.

        Returns:
            list of EvacuationRoute objects.
        """
        recommended_exit, path = HazardAwareRouter.compute_safe_path(situation.zone_id, blocked_exits)

        route = EvacuationRoute(
            zone_id=situation.zone_id,
            occupant_count=situation.occupants,
            recommended_exit=recommended_exit,
            path=path,
            blocked_exits=blocked_exits,
            estimated_evacuation_min=3.5,
            hazard_avoided=True,
        )
        return [route]
