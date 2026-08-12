"""bayesian_confidence.py — Bayesian Confidence Engine for RCA investigations.

Implements Bayes' theorem:
  Posterior = (Likelihood × Prior) / Evidence

Supports per-source priors, logarithmic opinion pooling, explainable reports.
"""
from __future__ import annotations
import math
from typing import Any

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Evidence, EvidenceSource, Investigation,
    BayesianConfidenceReport, BayesianEvidenceBreakdown, PatternMatch,
)

log = get_logger("root_cause.evidence.bayesian")

_SOURCE_PRIORS: dict[str, float] = {
    EvidenceSource.SENSOR_INTELLIGENCE.value: 0.75,
    EvidenceSource.VISION_INTELLIGENCE.value: 0.80,
    EvidenceSource.KNOWLEDGE_GRAPH.value: 0.70,
    EvidenceSource.GRAPHRAG.value: 0.60,
    EvidenceSource.WORKFLOW_ENGINE.value: 0.55,
    EvidenceSource.INCIDENT_MANAGEMENT.value: 0.72,
    EvidenceSource.AUDIT_FRAMEWORK.value: 0.90,
    EvidenceSource.NOTIFICATION_FRAMEWORK.value: 0.50,
    EvidenceSource.SUPERVISOR.value: 0.85,
    EvidenceSource.EXTERNAL.value: 0.40,
}


class BayesianConfidenceEngine:
    """Computes Bayesian posterior confidence for RCA investigations."""

    def compute(
        self,
        investigation: Investigation | None,
        evidence_list: list[Evidence],
        pattern_matches: list[PatternMatch] | None = None,
        historical_confidence: float = 0.0,
    ) -> BayesianConfidenceReport:
        """Full Bayesian confidence report for an investigation."""
        inv_id = investigation.id if investigation is not None else "unknown"
        log.info(f"Computing Bayesian confidence for investigation {inv_id}")

        by_source: dict[str, list[Evidence]] = {}
        for ev in evidence_list:
            by_source.setdefault(ev.source.value, []).append(ev)

        breakdown = BayesianEvidenceBreakdown()
        source_posteriors: list[float] = []

        for source, evs in by_source.items():
            prior = _SOURCE_PRIORS.get(source, 0.5)
            likelihood = sum(e.confidence * e.reliability for e in evs) / len(evs)
            posterior = self._bayes_update(prior, likelihood)
            source_posteriors.append(posterior)

            if source == EvidenceSource.SENSOR_INTELLIGENCE.value:
                breakdown.sensor_prior = prior
                breakdown.sensor_likelihood = likelihood
                breakdown.sensor_posterior = posterior
            elif source == EvidenceSource.VISION_INTELLIGENCE.value:
                breakdown.vision_prior = prior
                breakdown.vision_likelihood = likelihood
                breakdown.vision_posterior = posterior
            elif source == EvidenceSource.KNOWLEDGE_GRAPH.value:
                breakdown.graph_prior = prior
                breakdown.graph_likelihood = likelihood
                breakdown.graph_posterior = posterior
            elif source == EvidenceSource.GRAPHRAG.value:
                breakdown.graphrag_prior = prior
                breakdown.graphrag_likelihood = likelihood
                breakdown.graphrag_posterior = posterior

        if historical_confidence > 0:
            hist_posterior = self._bayes_update(0.5, historical_confidence)
            breakdown.historical_prior = 0.5
            breakdown.historical_likelihood = historical_confidence
            breakdown.historical_posterior = hist_posterior
            source_posteriors.append(hist_posterior)

        pattern_prior = 0.0
        if pattern_matches:
            top_match = max(pattern_matches, key=lambda m: m.similarity_score)
            pattern_prior = top_match.confidence
        else:
            pattern_prior = 0.1

        fused = self._log_pool(source_posteriors) if source_posteriors else 0.0
        final_posterior = fused * 0.7 + pattern_prior * 0.2 + historical_confidence * 0.1
        final_posterior = min(1.0, max(0.0, final_posterior))

        overall_prior = sum(_SOURCE_PRIORS.get(src, 0.5) for src in by_source) / max(1, len(by_source))
        convergence = 1.0 - (max(source_posteriors) - min(source_posteriors)) if len(source_posteriors) > 1 else 1.0

        explanation = self._explain(
            overall_prior, fused, final_posterior, len(evidence_list),
            pattern_matches, historical_confidence, convergence,
        )

        return BayesianConfidenceReport(
            investigation_id=inv_id,
            prior_probability=round(overall_prior, 4),
            likelihood=round(fused, 4),
            posterior_probability=round(final_posterior, 4),
            evidence_breakdown=breakdown,
            pattern_prior=round(pattern_prior, 4),
            historical_confidence=round(historical_confidence, 4),
            fused_confidence=round(final_posterior, 4),
            explanation=explanation,
            evidence_count=len(evidence_list),
            convergence_score=round(max(0.0, convergence), 4),
        )

    @staticmethod
    def _bayes_update(prior: float, likelihood: float) -> float:
        """P(H|E) = P(E|H)*P(H) / [P(E|H)*P(H) + P(E|~H)*P(~H)]"""
        numerator = likelihood * prior
        denominator = numerator + (1.0 - likelihood) * (1.0 - prior)
        if denominator <= 0:
            return prior
        return numerator / denominator

    @staticmethod
    def _log_pool(posteriors: list[float], weights: list[float] | None = None) -> float:
        """Logarithmic opinion pooling: geometric mean of posteriors."""
        if not posteriors:
            return 0.0
        n = len(posteriors)
        if weights is None:
            weights = [1.0 / n] * n
        log_sum = sum(w * math.log(max(1e-9, p)) for w, p in zip(weights, posteriors))
        return math.exp(log_sum)

    @staticmethod
    def _explain(
        prior: float, likelihood: float, posterior: float,
        evidence_count: int, pattern_matches: list[PatternMatch] | None,
        historical_confidence: float, convergence: float,
    ) -> str:
        parts = [
            f"Bayesian posterior: {posterior:.3f} (prior={prior:.3f}, likelihood={likelihood:.3f}).",
            f"Based on {evidence_count} evidence items.",
        ]
        if pattern_matches:
            top = pattern_matches[0]
            parts.append(f"Top pattern match: '{top.pattern_name}' (similarity={top.similarity_score:.2f}).")
        if historical_confidence > 0:
            parts.append(f"Historical context confidence: {historical_confidence:.2f}.")
        if convergence >= 0.8:
            parts.append("High evidence convergence — strong agreement across sources.")
        elif convergence >= 0.5:
            parts.append("Moderate evidence convergence — some disagreement between sources.")
        else:
            parts.append("Low evidence convergence — significant disagreement between sources.")
        return " ".join(parts)
