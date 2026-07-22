"""
domain/enums.py — Shared vocabulary for the Vision module.

Every downstream module (Root Cause, Emergency, GraphRAG) consumes
VisionEvents that carry these typed labels.  Keeping them in a single
file makes future cross-module imports trivial.

Design rules
────────────
• Enums ONLY — no behaviour, no FastAPI/SQLAlchemy coupling.
• String values are the canonical wire-format used in Kafka events and
  Postgres rows; do NOT change them without a migration plan.
"""

from enum import Enum


# ── Risk Levels ───────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    """
    Standardised severity ladder shared by all ABHEDYA modules.

    LOW      — informational; no immediate action required.
    MEDIUM   — warrants monitoring or a non-urgent alert.
    HIGH     — requires prompt operator attention.
    CRITICAL — demands immediate automated or human response.
    """

    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def numeric(self) -> int:
        """Return an integer rank (useful for comparisons and sorting)."""
        return {
            RiskLevel.LOW:      1,
            RiskLevel.MEDIUM:   2,
            RiskLevel.HIGH:     3,
            RiskLevel.CRITICAL: 4,
        }[self]

    def __ge__(self, other: "RiskLevel") -> bool:  # type: ignore[override]
        return self.numeric >= other.numeric

    def __gt__(self, other: "RiskLevel") -> bool:  # type: ignore[override]
        return self.numeric > other.numeric

    def __le__(self, other: "RiskLevel") -> bool:  # type: ignore[override]
        return self.numeric <= other.numeric

    def __lt__(self, other: "RiskLevel") -> bool:  # type: ignore[override]
        return self.numeric < other.numeric


# ── Hazard Types ─────────────────────────────────────────────────────────────

class HazardType(str, Enum):
    """
    Canonical vocabulary of detectable safety hazards.

    Detectors (YOLO, RT-DETR, Grounding DINO …) must map their raw class
    labels to one of these values via the infrastructure mapper.  The
    domain never sees raw class strings.

    Positive presence         → PERSON, HELMET, VEST
    Absence / non-compliance  → NO_HELMET, NO_VEST
    Environmental hazard      → FIRE, SMOKE, CHEMICAL_SPILL
    Incident                  → FALL
    Equipment                 → MACHINERY
    """

    # Presence — compliant
    PERSON          = "PERSON"
    HELMET          = "HELMET"
    VEST            = "VEST"

    # Absence — non-compliant (negative detection)
    NO_HELMET       = "NO_HELMET"
    NO_VEST         = "NO_VEST"

    # Environmental hazards
    FIRE            = "FIRE"
    SMOKE           = "SMOKE"
    CHEMICAL_SPILL  = "CHEMICAL_SPILL"

    # Incidents
    FALL            = "FALL"

    # Equipment
    MACHINERY       = "MACHINERY"

    @property
    def is_compliance_violation(self) -> bool:
        """True if this hazard represents a PPE non-compliance event."""
        return self in {HazardType.NO_HELMET, HazardType.NO_VEST}

    @property
    def is_environmental(self) -> bool:
        """True if this hazard is an environmental / physical danger."""
        return self in {HazardType.FIRE, HazardType.SMOKE, HazardType.CHEMICAL_SPILL}

    @property
    def is_incident(self) -> bool:
        """True if this hazard represents an active incident."""
        return self in {HazardType.FALL}
