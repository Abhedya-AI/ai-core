"""
application/use_cases/calculate_risk.py — CalculateRiskUseCase

Responsibility (ONE thing only)
────────────────────────────────
Accept a list of Detection objects and return a (RiskScore, list[Hazard])
tuple by delegating to the domain RiskEngine.

This use case knows nothing about:
  • Images or detectors    (→ AnalyzeFrameUseCase)
  • Database               (→ SaveDetectionUseCase)
  • Kafka                  (→ PublishEventUseCase)

It answers exactly one question:
  "How dangerous is this set of detections?"
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.application.calculate_risk import RiskEngine
from app.modules.vision.application.exceptions import RiskCalculationError
from app.modules.vision.domain.entities import Detection, Hazard
from app.modules.vision.domain.value_objects import RiskScore

log = get_logger("vision.use_cases.calculate_risk")

# Shared engine instance — stateless, safe to reuse
_engine = RiskEngine()


class CalculateRiskUseCase:
    """
    Thin orchestration wrapper around the domain RiskEngine.

    Parameters (injected)
    ─────────────────────
    engine  Optional custom RiskEngine (defaults to shared instance).
            Useful for testing custom weight tables.

    Usage
    ─────
        risk_score, hazards = CalculateRiskUseCase().execute(detections)
    """

    def __init__(self, engine: RiskEngine | None = None) -> None:
        self._engine = engine or _engine

    def execute(
        self,
        detections: list[Detection],
    ) -> tuple[RiskScore, list[Hazard]]:
        """
        Compute the frame-level risk score and hazard list.

        Raises
        ──────
        RiskCalculationError  If the engine raises an unexpected error.
        """
        try:
            risk_score, hazards = self._engine.calculate(detections)
        except Exception as exc:
            raise RiskCalculationError(
                f"RiskEngine failed on {len(detections)} detections: {exc}",
                detail=str(exc),
            ) from exc

        log.info(
            f"CalculateRiskUseCase: {len(detections)} detection(s) → "
            f"score={risk_score.score:.3f} level={risk_score.level.value}"
        )

        return risk_score, hazards
