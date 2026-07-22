"""
domain/entities.py — Core domain entities for the Vision module.

Entities have identity and lifecycle.  They live in the domain layer and
carry no infrastructure dependencies (no SQLAlchemy, no Pydantic
validators, no HTTP concerns).

Entities
────────
Detection   A single object detected in one frame.
Hazard      A domain-interpreted hazard derived from one or more detections.
VisionEvent The aggregate event published after a frame is analysed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.modules.vision.domain.enums import HazardType, RiskLevel
from app.modules.vision.domain.enums.detection_status import DetectionStatus
from app.modules.vision.domain.value_objects import BoundingBox, RiskScore


def _now_utc() -> datetime:
    """Return the current time in UTC with timezone info."""
    return datetime.now(tz=timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ── Detection ─────────────────────────────────────────────────────────────────

@dataclass
class Detection:
    """
    A single object detected in a frame by the underlying vision model.

    This is the direct output of the infrastructure → domain mapping step.
    Every field here is in domain language — no raw YOLO class IDs.

    Attributes
    ──────────
    id              Unique identifier (UUID string).
    hazard_type     The classified hazard category.
    confidence      Model confidence score ∈ [0, 1].
    bounding_box    Normalised location in the image.
    frame_id        Caller-supplied identifier for the source frame.
    camera_id       Identifier of the camera that captured the frame.
    status          Lifecycle state of this detection (default: PENDING).
    timestamp       When this detection was produced.
    image_path      Optional path to the persisted frame image.
    """

    hazard_type:  HazardType
    confidence:   float
    bounding_box: BoundingBox
    frame_id:     str
    camera_id:    str

    id:         str             = field(default_factory=_new_uuid)
    status:     DetectionStatus = field(default=DetectionStatus.PENDING)
    timestamp:  datetime        = field(default_factory=_now_utc)
    image_path: str | None      = field(default=None)

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Detection.confidence must be in [0, 1]; got {self.confidence}"
            )

    # ── Domain helpers ────────────────────────────────────────────────────────

    @property
    def is_high_confidence(self) -> bool:
        """True if the model is highly certain of this detection (≥ 0.75)."""
        return self.confidence >= 0.75

    @property
    def is_critical_hazard(self) -> bool:
        """True if the detected hazard is inherently critical (fire, chemical, fall)."""
        return self.hazard_type in {
            HazardType.FIRE,
            HazardType.CHEMICAL_SPILL,
            HazardType.FALL,
        }

    @property
    def is_pending(self) -> bool:
        return self.status == DetectionStatus.PENDING

    @property
    def is_verified(self) -> bool:
        return self.status == DetectionStatus.VERIFIED

    def verify(self) -> "Detection":
        """Return a new Detection with status=VERIFIED (immutable-style)."""
        from dataclasses import replace
        return replace(self, status=DetectionStatus.VERIFIED)

    def reject(self) -> "Detection":
        """Return a new Detection with status=REJECTED."""
        from dataclasses import replace
        return replace(self, status=DetectionStatus.REJECTED)


# ── Hazard ────────────────────────────────────────────────────────────────────

@dataclass
class Hazard:
    """
    A domain-level hazard — may aggregate multiple raw detections.

    Whereas Detection maps 1-to-1 with a model output box, a Hazard
    can represent a higher-level understanding, e.g. two overlapping
    NO_HELMET detections collapsed into a single Hazard, or a FALL
    derived from posture analysis spanning several detections.

    In Milestone 1 the mapper produces one Hazard per Detection;
    future milestones may introduce clustering / aggregation logic here.

    Attributes
    ──────────
    id              Unique identifier (UUID string).
    hazard_type     Canonical hazard category.
    confidence      Aggregated confidence for this hazard.
    risk_level      Discrete severity assessment for this hazard alone.
    bounding_box    Bounding region (union of contributing detections).
    source_detection_ids
                    Detection IDs that contributed to this hazard.
    description     Human-readable summary.
    """

    hazard_type:          HazardType
    confidence:           float
    risk_level:           RiskLevel
    bounding_box:         BoundingBox
    source_detection_ids: list[str] = field(default_factory=list)
    description:          str       = ""

    id:        str      = field(default_factory=_new_uuid)
    timestamp: datetime = field(default_factory=_now_utc)

    @property
    def requires_immediate_action(self) -> bool:
        return self.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}


# ── VisionEvent ───────────────────────────────────────────────────────────────

@dataclass
class VisionEvent:
    """
    The aggregate event produced after a full frame analysis.

    This is the object that is:
      • persisted in PostgreSQL (via repository)
      • published to Kafka (via publisher)
      • returned in the API response

    All downstream modules (Root Cause, Emergency, GraphRAG) consume
    VisionEvents — the contract is defined by the fields below.

    Attributes
    ──────────
    event_id        Unique identifier (UUID string).
    timestamp       UTC time of analysis.
    camera_id       Source camera identifier.
    frame_id        Caller-supplied frame identifier.
    detections      All domain detections for this frame.
    hazards         Domain hazards derived from the detections.
    risk_score      Aggregated risk score for the frame.
    image_path      Optional persisted image path.
    location        Optional free-text or coordinate string.
    metadata        Extensible key-value bag for future use.
    """

    camera_id:   str
    frame_id:    str
    detections:  list[Detection]
    hazards:     list[Hazard]
    risk_score:  RiskScore

    event_id:    str        = field(default_factory=_new_uuid)
    timestamp:   datetime   = field(default_factory=_now_utc)
    image_path:  str | None = field(default=None)
    location:    str | None = field(default=None)
    metadata:    dict       = field(default_factory=dict)

    # ── Convenience accessors ─────────────────────────────────────────────────

    @property
    def detection_count(self) -> int:
        return len(self.detections)

    @property
    def hazard_count(self) -> int:
        return len(self.hazards)

    @property
    def is_critical(self) -> bool:
        return self.risk_score.is_critical

    @property
    def actionable_hazards(self) -> list[Hazard]:
        """Return only hazards that require immediate action."""
        return [h for h in self.hazards if h.requires_immediate_action]

    @property
    def unique_hazard_types(self) -> set[HazardType]:
        """Set of distinct hazard types found in this event."""
        return {h.hazard_type for h in self.hazards}

    def summary(self) -> str:
        """One-liner for logging and monitoring."""
        return (
            f"VisionEvent[{self.event_id[:8]}] "
            f"camera={self.camera_id} "
            f"detections={self.detection_count} "
            f"hazards={self.hazard_count} "
            f"risk={self.risk_score.level.value}({self.risk_score.score:.2f})"
        )
