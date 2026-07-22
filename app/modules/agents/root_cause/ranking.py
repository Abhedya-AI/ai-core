"""ranking.py — Phase 6: Hypothesis Ranking Engine."""

from app.modules.agents.root_cause.models import Hypothesis


class HypothesisRanker:
    """Phase 6: Ranks candidate hypotheses by confidence score descending."""

    @staticmethod
    def rank_hypotheses(hypotheses: list[Hypothesis]) -> list[Hypothesis]:
        """
        Sort and assign ranks to hypotheses.

        Returns:
            list of Hypothesis objects sorted by confidence_score descending.
        """
        sorted_h = sorted(hypotheses, key=lambda x: x.confidence_score, reverse=True)
        for idx, h in enumerate(sorted_h, 1):
            h.rank = idx
        return sorted_h
