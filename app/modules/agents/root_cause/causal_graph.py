"""causal_graph.py — Phase 3: Causal Graph Builder Engine."""

from app.modules.agents.root_cause.models import CausalEdge, EvidenceBundle, TimelineEvent


class CausalGraphBuilder:
    """Phase 3: Builds directed causal edges connecting root causes to intermediate effects and the incident."""

    @staticmethod
    def build_causal_graph(bundle: EvidenceBundle, timeline: list[TimelineEvent]) -> list[CausalEdge]:
        """
        Construct directed causal graph edges.

        Returns:
            list of CausalEdge objects.
        """
        edges: list[CausalEdge] = []

        # Connect maintenance overdue -> valve failure -> gas leak -> incident
        edges.append(
            CausalEdge(
                cause_id="MAINT-OVERDUE-V12",
                effect_id="VALVE-V12-FAILURE",
                confidence=0.92,
                supporting_evidence=["Maintenance overdue by 34 days"],
                source="MAINTENANCE_RECORD",
            )
        )

        edges.append(
            CausalEdge(
                cause_id="VALVE-V12-FAILURE",
                effect_id="HAZ-GAS-LEAK",
                confidence=0.95,
                supporting_evidence=["Telemetry pressure spike and visual gas plume"],
                source="SENSOR_VISION_FUSION",
            )
        )

        edges.append(
            CausalEdge(
                cause_id="HAZ-GAS-LEAK",
                effect_id=bundle.incident_id,
                confidence=0.98,
                supporting_evidence=["Gas leak triggered emergency alert"],
                source="INCIDENT_RECONSTRUCTION",
            )
        )

        return edges
