"""resource_allocator.py — Phase 5: Resource Allocation Engine."""

from app.modules.agents.emergency.models import ResourceAssignment, SituationModel


class ResourceAllocator:
    """Phase 5: Determines responder and equipment allocations (Fire, Medical, Hazmat, Maintenance teams)."""

    @staticmethod
    def allocate_resources(situation: SituationModel) -> list[ResourceAssignment]:
        """
        Allocate responders based on active hazards.

        Returns:
            list of ResourceAssignment objects.
        """
        assignments = []
        hazards = [h.upper() for h in situation.active_hazards]

        if any("FIRE" in h or "SMOKE" in h for h in hazards):
            assignments.append(
                ResourceAssignment(
                    resource_id="FIRE-TEAM-ALPHA",
                    resource_type="FIRE_TEAM",
                    assigned_zone=situation.zone_id,
                    priority=1,
                    eta_minutes=2.0,
                    status="DISPATCHED",
                )
            )

        if situation.occupants > 0:
            assignments.append(
                ResourceAssignment(
                    resource_id="MEDICAL-TEAM-1",
                    resource_type="MEDICAL_TEAM",
                    assigned_zone=situation.zone_id,
                    priority=1,
                    eta_minutes=2.5,
                    status="DISPATCHED",
                )
            )

        if any("GAS" in h or "CHEMICAL" in h for h in hazards):
            assignments.append(
                ResourceAssignment(
                    resource_id="HAZMAT-UNIT-02",
                    resource_type="HAZMAT_TEAM",
                    assigned_zone=situation.zone_id,
                    priority=2,
                    eta_minutes=4.0,
                    status="EN_ROUTE",
                )
            )

        return assignments
