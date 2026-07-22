"""optimizer.py — Phase 7: Dynamic Continuous Replanning & Optimization Engine."""

from app.core.logging import get_logger
from app.modules.agents.emergency.models import EmergencyPlan, EvacuationRoute, SituationModel
from app.modules.agents.emergency.routing import HazardAwareRouter

log = get_logger("agents.emergency.optimizer")


class EmergencyOptimizer:
    """Phase 7: Adapts emergency plan and evacuation routes dynamically when new hazards or blocked exits arrive."""

    @staticmethod
    def optimize_plan(plan: EmergencyPlan, situation: SituationModel, new_blocked_exit: str | None = None) -> EmergencyPlan:
        """
        Recompute routes dynamically if exit status changes without discarding overall response plan.

        Returns:
            Updated EmergencyPlan object.
        """
        if not new_blocked_exit:
            return plan

        log.warning(f"Dynamic replanning triggered: new blocked exit '{new_blocked_exit}' detected")

        updated_routes = []
        for r in plan.evacuation_routes:
            blocked = list(dict.fromkeys(r.blocked_exits + [new_blocked_exit]))
            recommended_exit, path = HazardAwareRouter.compute_safe_path(r.zone_id, blocked)

            updated_routes.append(
                EvacuationRoute(
                    zone_id=r.zone_id,
                    occupant_count=r.occupant_count,
                    recommended_exit=recommended_exit,
                    path=path,
                    blocked_exits=blocked,
                    estimated_evacuation_min=4.5,
                    hazard_avoided=True,
                )
            )

        plan.evacuation_routes = updated_routes
        plan.is_replanned = True
        return plan
