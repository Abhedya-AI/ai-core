"""conflict_resolver.py — Multi-Agent Output Conflict Resolver.

Identifies conflicting findings across agents (e.g. Vision detects Fire vs. Prediction says Low Risk)
and resolves them using confidence weighting, source authority rules, or human review flags.
"""

from typing import Any

from app.core.logging import get_logger
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.supervisor.models import ConflictRecord, ConflictResolutionStrategy

log = get_logger("agents.supervisor.conflict_resolver")

# Source authority hierarchy: Vision > Sensor/Risk > Prediction
_AUTHORITY_RANK: dict[str, int] = {
    "VisionAgent": 10,
    "EmergencyAgent": 9,
    "RiskAgent": 8,
    "RootCauseAgent": 7,
    "ComplianceAgent": 6,
    "PredictionAgent": 5,
    "DocumentAgent": 4,
}


class ConflictResolver:
    """
    Detects and resolves contradicting claims between executed agents.
    """

    def resolve_conflicts(
        self,
        results: list[AgentResult],
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.SOURCE_AUTHORITY,
    ) -> list[ConflictRecord]:
        """
        Inspect agent results for conflicting claims and apply resolution strategy.

        Args:
            results: List of completed AgentResult objects.
            strategy: Resolution strategy enum.

        Returns:
            List of ConflictRecord objects describing resolved conflicts.
        """
        conflicts: list[ConflictRecord] = []
        result_map = {r.agent_name: r for r in results if r.success}

        # Check: Vision detected hazard vs Prediction low risk
        vision_res = result_map.get("VisionAgent")
        pred_res = result_map.get("PredictionAgent")

        if vision_res and pred_res:
            vision_detected = any(
                e.event_type in ("FireDetected", "SmokeDetected", "SpillDetected")
                for e in vision_res.events
            )
            pred_risk = pred_res.output_data.get("risk_score", 0.0)

            if vision_detected and (isinstance(pred_risk, (int, float)) and pred_risk < 30.0):
                log.warning("ConflictResolver: detected conflict between VisionAgent (Hazard) and PredictionAgent (Low Risk)")

                if strategy == ConflictResolutionStrategy.SOURCE_AUTHORITY:
                    winner = "VisionAgent"
                    resolved_out = {"hazard_active": True, "source": "VisionAgent"}
                    rationale = "Vision direct observation overrides predictive model output under SOURCE_AUTHORITY strategy."
                else:
                    winner = "VisionAgent" if vision_res.confidence >= pred_res.confidence else "PredictionAgent"
                    resolved_out = {"hazard_active": True}
                    rationale = f"Resolved via HIGHEST_CONFIDENCE (Vision={vision_res.confidence}, Pred={pred_res.confidence})"

                rec = ConflictRecord(
                    agent_a="VisionAgent",
                    output_a={"hazard_detected": True},
                    confidence_a=vision_res.confidence,
                    agent_b="PredictionAgent",
                    output_b={"risk_score": pred_risk},
                    confidence_b=pred_res.confidence,
                    resolution_strategy=strategy,
                    winning_agent=winner,
                    resolved_output=resolved_out,
                    rationale=rationale,
                )
                conflicts.append(rec)

        log.info(f"ConflictResolver: evaluated {len(results)} agent outputs → {len(conflicts)} conflict(s) resolved.")
        return conflicts
