"""recommendation_feedback.py — Recommendation feedback tracking service."""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    RecommendationFeedback, FeedbackOutcome, LessonLearned,
)
from app.modules.root_cause.feedback.feedback_repository import FeedbackRepository

log = get_logger("root_cause.feedback.tracker")


class RecommendationFeedbackTracker:
    """Tracks recommendation outcomes and generates effectiveness metrics."""

    def __init__(self, repo: FeedbackRepository | None = None) -> None:
        self.repo = repo or FeedbackRepository()

    async def submit(
        self,
        recommendation_id: str,
        investigation_id: str,
        outcome: FeedbackOutcome,
        impact_description: str = "",
        executed_by: str = "",
        effectiveness_score: float = 0.0,
        cost_actual: str = "",
    ) -> RecommendationFeedback:
        """Submit feedback for a recommendation outcome."""
        score = effectiveness_score or self._infer_effectiveness(outcome)
        feedback = RecommendationFeedback(
            recommendation_id=recommendation_id,
            investigation_id=investigation_id,
            outcome=outcome,
            impact_description=impact_description,
            executed_by=executed_by,
            effectiveness_score=score,
            cost_actual=cost_actual,
        )
        await self.repo.save(feedback)
        log.info(f"Feedback submitted: recommendation={recommendation_id}, outcome={outcome.value}")
        return feedback

    async def get_for_investigation(
        self, investigation_id: str
    ) -> list[RecommendationFeedback]:
        return await self.repo.list_by_investigation(investigation_id)

    async def get_effectiveness_rate(self) -> float:
        return await self.repo.compute_effectiveness_rate()

    async def get_recent(self, limit: int = 50) -> list[RecommendationFeedback]:
        return await self.repo.list_recent(limit=limit)

    def generate_lessons_from_feedback(
        self, feedback: RecommendationFeedback
    ) -> list[LessonLearned]:
        """Generate lessons learned from feedback on recommendation outcomes."""
        # Auto-infer effectiveness score from outcome when not explicitly provided
        if feedback.effectiveness_score == 0.0:
            feedback.effectiveness_score = self._infer_effectiveness(feedback.outcome)
        lessons = []
        if feedback.outcome in (FeedbackOutcome.SUCCESSFUL, FeedbackOutcome.EXECUTED):
            lessons.append(LessonLearned(
                investigation_id=feedback.investigation_id,
                lesson_text=(
                    f"Recommendation '{feedback.recommendation_id}' was {feedback.outcome.value}. "
                    f"{feedback.impact_description or 'Positive outcome recorded.'}"
                ),
                lesson_category="RECOMMENDATION_SUCCESS",
                confidence=feedback.effectiveness_score or 0.7,
                tags=["recommendation", "effective", feedback.outcome.value.lower()],
            ))
        elif feedback.outcome in (FeedbackOutcome.FAILED, FeedbackOutcome.IGNORED):
            lessons.append(LessonLearned(
                investigation_id=feedback.investigation_id,
                lesson_text=(
                    f"Recommendation '{feedback.recommendation_id}' outcome: {feedback.outcome.value}. "
                    f"{feedback.impact_description or 'Review recommendation criteria.'}"
                ),
                lesson_category="RECOMMENDATION_FAILURE",
                confidence=0.5,
                tags=["recommendation", "ineffective", feedback.outcome.value.lower()],
            ))
        return lessons

    @staticmethod
    def _infer_effectiveness(outcome: FeedbackOutcome) -> float:
        """Heuristic effectiveness score from outcome."""
        _MAP = {
            FeedbackOutcome.SUCCESSFUL: 1.0,
            FeedbackOutcome.EXECUTED: 0.7,
            FeedbackOutcome.PARTIAL: 0.5,
            FeedbackOutcome.DELAYED: 0.3,
            FeedbackOutcome.FAILED: 0.0,
            FeedbackOutcome.IGNORED: 0.0,
        }
        return _MAP.get(outcome, 0.5)
