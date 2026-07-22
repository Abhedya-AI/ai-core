"""
domain/value_objects/risk_score.py — Business representation of calculated risk.

Design
──────
• RiskScore is a pure value object — it stores validated risk information.
• It does NOT decide how risk is calculated.  That responsibility belongs
  to the Risk Policy Engine (domain/policies/risk_policy.py, Milestone 2+).

Separation of concerns
───────────────────────
    Detection
          │
          ▼
    RiskPolicy          ← decides the score and level
          │
          ▼
    RiskScore(score=0.87, level=HIGH, reason="Active fire detected.")

This means:
• Changing a safety rule (e.g. NO_HELMET → HIGH instead of MEDIUM)
  only touches risk_policy.py — never this file.
• RiskScore is safe to test independently of any scoring logic.

Why frozen Pydantic?
────────────────────
• Immutable after construction — no accidental mutation between layers.
• Pydantic validates score ∈ [0, 1] at construction time.
• FastAPI serialises it to JSON directly without extra adapters.
"""

from pydantic import BaseModel, ConfigDict, Field

from app.modules.vision.domain.enums import RiskLevel


class RiskScore(BaseModel):
    """
    Business representation of calculated risk.

    Attributes
    ──────────
    score   Continuous risk value ∈ [0.0, 1.0].  Higher = more dangerous.
    level   Discretised severity level (set by the Risk Policy Engine).
    reason  Human-readable explanation of what drove this score.
            Used in operator dashboards and audit logs.
    """

    model_config = ConfigDict(frozen=True)

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Continuous risk score in [0, 1].",
    )

    level: RiskLevel = Field(
        ...,
        description="Discrete severity level.",
    )

    reason: str = Field(
        default="",
        max_length=500,
        description="Human-readable explanation of the risk score.",
    )

    # ── Domain helpers ────────────────────────────────────────────────────────

    @property
    def percentage(self) -> float:
        """Score expressed as a rounded percentage (e.g. 0.873 → 87.3)."""
        return round(self.score * 100, 2)

    @property
    def is_critical(self) -> bool:
        """True when the risk level is CRITICAL — demands immediate response."""
        return self.level == RiskLevel.CRITICAL
