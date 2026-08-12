"""recommendation_learning.py — Feedback-driven pattern confidence update engine."""
from __future__ import annotations

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import RecommendationFeedback, FeedbackOutcome

log = get_logger("root_cause.feedback.learning")


class RecommendationLearningEngine:
    """Updates pattern library confidence based on recommendation feedback outcomes."""

    # Learning rates per outcome
    _OUTCOME_DELTA: dict[FeedbackOutcome, float] = {
        FeedbackOutcome.SUCCESSFUL: +0.05,
        FeedbackOutcome.EXECUTED: +0.02,
        FeedbackOutcome.PARTIAL: +0.01,
        FeedbackOutcome.DELAYED: -0.01,
        FeedbackOutcome.FAILED: -0.04,
        FeedbackOutcome.IGNORED: -0.02,
    }

    def compute_confidence_delta(
        self,
        feedback: RecommendationFeedback | FeedbackOutcome,
    ) -> float:
        """Compute the confidence adjustment. Accepts a FeedbackOutcome enum or a full RecommendationFeedback object."""
        if isinstance(feedback, FeedbackOutcome):
            return round(self._OUTCOME_DELTA.get(feedback, 0.0), 4)
        base_delta = self._OUTCOME_DELTA.get(feedback.outcome, 0.0)
        # Scale by effectiveness score
        effectiveness_weight = max(0.5, feedback.effectiveness_score)
        delta = base_delta * effectiveness_weight
        return round(delta, 4)

    def compute_batch_delta(
        self, feedback_list: list[RecommendationFeedback]
    ) -> float:
        """Aggregate confidence delta from a batch of feedback items."""
        if not feedback_list:
            return 0.0
        total = sum(self.compute_confidence_delta(fb) for fb in feedback_list)
        return round(total / len(feedback_list), 4)

    def should_escalate(
        self, feedback_list: list[RecommendationFeedback], threshold: int = 3
    ) -> bool:
        """True if too many consecutive FAILED/IGNORED outcomes — pattern review needed."""
        bad_outcomes = {
            FeedbackOutcome.FAILED, FeedbackOutcome.IGNORED
        }
        bad_count = sum(1 for fb in feedback_list if fb.outcome in bad_outcomes)
        return bad_count >= threshold
