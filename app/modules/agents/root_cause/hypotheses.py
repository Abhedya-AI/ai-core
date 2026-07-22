"""hypotheses.py — Phase 4: Hypothesis Generation Engine."""

from app.modules.agents.root_cause.models import CausalEdge, EvidenceBundle, Hypothesis


class HypothesisGenerator:
    """Phase 4: Generates multiple competing root cause hypotheses to avoid single-cause bias."""

    @staticmethod
    def generate_hypotheses(bundle: EvidenceBundle, causal_edges: list[CausalEdge]) -> list[Hypothesis]:
        """
        Generate candidate root cause hypotheses.

        Returns:
            list of Hypothesis objects.
        """
        h1 = Hypothesis(
            hypothesis_id="HYP-A",
            root_cause_candidate="VALVE-V12-FAILURE",
            description="Primary isolation valve V-12 mechanical seal failure due to overdue maintenance.",
            causal_path=["MAINT-OVERDUE-V12", "VALVE-V12-FAILURE", "HAZ-GAS-LEAK", bundle.incident_id],
            supporting_evidence=[
                "Pressure exceeded operating threshold 5 mins before incident",
                "Maintenance overdue by 34 days",
                "Vision detection of gas plume prior to ignition",
            ],
        )

        h2 = Hypothesis(
            hypothesis_id="HYP-B",
            root_cause_candidate="TELEMETRY-SENSOR-MALFUNCTION",
            description="Telemetry pressure sensor calibration drift causing false readings and delayed valve closure.",
            causal_path=["SENSOR-DRIFT", "DELAYED-ACTION", bundle.incident_id],
            supporting_evidence=["Sensor calibration log overdue by 60 days"],
        )

        h3 = Hypothesis(
            hypothesis_id="HYP-C",
            root_cause_candidate="OPERATOR-PROCEDURAL-ERROR",
            description="Operator manual override error during shift transition.",
            causal_path=["OPERATOR-OVERRIDE", bundle.incident_id],
            supporting_evidence=["Shift changeover coincided with incident timestamp"],
        )

        return [h1, h2, h3]
