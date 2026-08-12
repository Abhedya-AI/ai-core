"""
application/dto/analyze_response.py — FrameAnalysisResult DTO.

FrameAnalysisResult is the rich return type of AnalyzeFrameUseCase.
It carries everything the orchestrator and API need:

  • The raw detections (for downstream use cases)
  • The computed hazards and risk score
  • Operational metrics (processing_time_ms, model_version)
  • The assembled VisionEvent aggregate

Why a DTO and not just a VisionEvent?
──────────────────────────────────────
VisionEvent is a domain aggregate — frozen, validated, published to Kafka.
FrameAnalysisResult is a pipeline artefact — it holds intermediate state
(processing_time_ms, model_version) that belongs to the infrastructure
layer, not the domain.  The API and orchestrator work with this DTO;
only the Kafka topic sees the VisionEvent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.vision.domain.entities import Detection, Hazard, VisionEvent
    from app.modules.vision.domain.enums import RiskLevel
    from app.modules.vision.domain.value_objects import RiskScore


@dataclass(frozen=True)
class FrameAnalysisResult:
    """
    Immutable result object returned by AnalyzeFrameUseCase.

    Fields
    ──────
    frame_id            Identifier of the analysed frame.
    camera_id           Source camera identifier.
    processing_time_ms  Wall-clock time for the full analysis pipeline (ms).
    detections          Raw Detection domain objects from the detector + mapper.
    hazards             Deduped, weighted Hazard list from the RiskEngine.
    risk_score          Aggregated frame-level RiskScore.
    highest_risk        Convenience alias → risk_score.level.
    model_version       Detector model version string (e.g. "yolov8n-safety-v2").
    event               The assembled VisionEvent aggregate (may be None before
                        ProcessDetectionUseCase saves and sets it).
    """

    frame_id:           str
    camera_id:          str
    processing_time_ms: float
    detections:         list                = field(default_factory=list)
    hazards:            list                = field(default_factory=list)
    risk_score:         object | None       = None   # RiskScore
    highest_risk:       object | None       = None   # RiskLevel
    model_version:      str                 = "unknown"
    event:              object | None       = None   # VisionEvent

    # ── Convenience properties ─────────────────────────────────────────────────

    @property
    def detection_count(self) -> int:
        return len(self.detections)

    @property
    def hazard_count(self) -> int:
        return len(self.hazards)

    @property
    def is_critical(self) -> bool:
        """True when the risk level is CRITICAL."""
        if self.event is not None:
            return self.event.is_critical
        if self.risk_score is not None:
            from app.modules.vision.domain.enums import RiskLevel
            return self.risk_score.level == RiskLevel.CRITICAL
        return False

    def summary(self) -> str:
        """One-line human-readable summary for logging."""
        risk_label = (
            self.risk_score.level.value if self.risk_score else "N/A"
        )
        return (
            f"FrameAnalysisResult "
            f"camera={self.camera_id} "
            f"frame={self.frame_id} "
            f"detections={self.detection_count} "
            f"hazards={self.hazard_count} "
            f"risk={risk_label} "
            f"time={self.processing_time_ms:.1f}ms "
            f"model={self.model_version}"
        )
