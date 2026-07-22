"""
domain/enums/detection_status.py — Lifecycle states for a detection record.

A Detection moves through these states as human reviewers and downstream
systems process it.  The transitions are governed by the domain, not the
persistence layer.

State machine
─────────────
              ┌─────────────────────────────────┐
              ▼                                 │
    PENDING ──┬──► VERIFIED                     │
              │                                 │
              └──► REJECTED                     │
                       │                        │
                       └──► ARCHIVED ───────────┘
                                    (any state can archive)
"""

from enum import Enum


class DetectionStatus(str, Enum):
    """Lifecycle state of a detection."""

    PENDING  = "PENDING"
    """Default state — awaiting review or automated confirmation."""

    VERIFIED = "VERIFIED"
    """Confirmed as a genuine hazard by a human or downstream module."""

    REJECTED = "REJECTED"
    """Determined to be a false positive."""

    ARCHIVED = "ARCHIVED"
    """Soft-deleted — retained for audit but excluded from active queries."""

    @property
    def is_active(self) -> bool:
        """True for states that appear in operational dashboards."""
        return self in {DetectionStatus.PENDING, DetectionStatus.VERIFIED}

    @property
    def is_terminal(self) -> bool:
        """True when no further state transitions are expected."""
        return self in {DetectionStatus.REJECTED, DetectionStatus.ARCHIVED}
