"""situation_model.py — Phase 2: Shared Operational Situation Model Builder."""

from app.modules.agents.emergency.models import IncidentState, SituationModel
from app.modules.agents.emergency.providers import MapEmergencyProvider


class SituationModelBuilder:
    """Phase 2: Builds a unified operational picture driving all downstream planning and resource allocation."""

    @staticmethod
    def build_situation_model(state: IncidentState) -> SituationModel:
        zone_map = MapEmergencyProvider.get_zone_map(state.affected_zone)
        all_exits = zone_map.get("available_exits", ["EXIT-A", "EXIT-C", "EXIT-D"])

        # Filter out blocked exits
        accessible_exits = [e for e in all_exits if e not in state.blocked_exits]

        threat_score = 95.0 if state.severity == "CRITICAL" else 75.0

        return SituationModel(
            zone_id=state.affected_zone,
            occupants=state.affected_workers_count,
            active_hazards=state.active_hazards,
            accessible_exits=accessible_exits,
            hazard_spread_risk=f"Predicted hazard spread reaches adjacent corridor in {state.prediction_time_horizon_min} min",
            overall_threat_score=threat_score,
        )
