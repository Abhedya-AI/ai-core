"""
domain/enums/hazard_type.py — Canonical vocabulary of detectable safety hazards.

Every detector implementation must map its raw class labels to one of
these values via the infrastructure mapper.  The domain never sees raw
class strings or model-specific IDs.

Design note — future Risk Policy Engine
────────────────────────────────────────
The mapping of HazardType → RiskLevel intentionally does NOT live here.
It will live in:

    domain/policies/risk_policy.py

Benefits:
• Business rules are centralised.
• Safety policy changes (e.g. NO_HELMET escalated to HIGH) happen in
  one place without touching this enum or any use-case.
"""

from enum import Enum


class HazardType(str, Enum):
    # ── Presence detections (compliant / informational) ───────────────────────
    PERSON         = "PERSON"
    HELMET         = "HELMET"
    SAFETY_VEST    = "SAFETY_VEST"
    MASK           = "MASK"
    GLOVES         = "GLOVES"
    GOGGLES        = "GOGGLES"
    WORKER         = "WORKER"

    # ── PPE non-compliance ────────────────────────────────────────────────────
    NO_HELMET      = "NO_HELMET"
    NO_SAFETY_VEST = "NO_SAFETY_VEST"
    NO_MASK        = "NO_MASK"
    NO_GLOVES      = "NO_GLOVES"
    NO_GOGGLES     = "NO_GOGGLES"

    # ── Environmental hazards ─────────────────────────────────────────────────
    FIRE           = "FIRE"
    SMOKE          = "SMOKE"

    # ── Spills and contamination ──────────────────────────────────────────────
    CHEMICAL_SPILL = "CHEMICAL_SPILL"

    # ── Incidents ─────────────────────────────────────────────────────────────
    FALL           = "FALL"

    # ── Heavy equipment ───────────────────────────────────────────────────────
    FORKLIFT       = "FORKLIFT"
    CRANE          = "CRANE"
    TRUCK          = "TRUCK"

    # ── Behavioral ────────────────────────────────────────────────────────────
    RESTRICTED_ZONE_ENTRY = "RESTRICTED_ZONE_ENTRY"

    # ── Equipment (legacy) ────────────────────────────────────────────────────
    MACHINERY      = "MACHINERY"

    # ── Fallback ──────────────────────────────────────────────────────────────
    UNKNOWN        = "UNKNOWN"

    # ── Domain helpers ────────────────────────────────────────────────────────

    @property
    def is_compliance_violation(self) -> bool:
        """True if this hazard represents a PPE non-compliance event."""
        return self in {
            HazardType.NO_HELMET, HazardType.NO_SAFETY_VEST,
            HazardType.NO_MASK, HazardType.NO_GLOVES, HazardType.NO_GOGGLES,
        }

    @property
    def is_environmental(self) -> bool:
        """True if this hazard is an environmental / physical danger."""
        return self in {HazardType.FIRE, HazardType.SMOKE, HazardType.CHEMICAL_SPILL}

    @property
    def is_incident(self) -> bool:
        """True if this hazard represents an active incident."""
        return self in {HazardType.FALL}

    @property
    def is_compliant_presence(self) -> bool:
        """True for detections that confirm PPE compliance."""
        return self in {
            HazardType.HELMET, HazardType.SAFETY_VEST,
            HazardType.MASK, HazardType.GLOVES, HazardType.GOGGLES,
        }

    @property
    def is_equipment(self) -> bool:
        """True for heavy equipment detections."""
        return self in {HazardType.FORKLIFT, HazardType.CRANE, HazardType.TRUCK, HazardType.MACHINERY}
