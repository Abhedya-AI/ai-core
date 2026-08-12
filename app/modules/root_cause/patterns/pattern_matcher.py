"""pattern_matcher.py — Evidence-to-pattern similarity matching engine."""
from __future__ import annotations

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Evidence, FailurePattern, PatternMatch, Hypothesis,
)
from app.modules.root_cause.patterns.pattern_library import PatternLibrary

log = get_logger("root_cause.patterns.matcher")


class PatternMatcher:
    """Matches investigation evidence against the failure pattern library."""

    def __init__(self, library: PatternLibrary | None = None) -> None:
        self.library = library or PatternLibrary()

    def match(
        self,
        evidence_list: list[Evidence],
        hypotheses: list[Hypothesis] | None = None,
        top_k: int = 5,
        min_similarity: float = 0.2,
    ) -> list[PatternMatch]:
        """Match evidence against all patterns, return ranked matches."""
        log.info(f"Matching {len(evidence_list)} evidence items against pattern library")
        evidence_types = {e.evidence_type.value for e in evidence_list}
        sources = {e.source.value for e in evidence_list}
        severities = {e.severity for e in evidence_list}

        matches: list[PatternMatch] = []
        for pattern in self.library.list_patterns(limit=100):
            score = self._compute_similarity(
                pattern, evidence_types, sources, severities, evidence_list,
            )
            if score >= min_similarity:
                required_ev_types = set(pattern.required_evidence_types)
                missing = list(required_ev_types - evidence_types)
                matched_count = len([e for e in evidence_list if e.evidence_type.value in required_ev_types])
                confidence = score * pattern.prior_probability * (1 + pattern.historical_matches * 0.01)
                confidence = min(1.0, confidence * 10)
                matches.append(PatternMatch(
                    pattern_id=pattern.id,
                    pattern_name=pattern.name,
                    pattern_type=pattern.pattern_type,
                    similarity_score=round(score, 4),
                    confidence=round(min(1.0, confidence), 4),
                    matched_evidence_count=matched_count,
                    missing_evidence_types=missing,
                    match_explanation=self._explain(pattern, score, missing),
                ))

        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        return matches[:top_k]

    def _compute_similarity(
        self,
        pattern: FailurePattern,
        evidence_types: set[str],
        sources: set[str],
        severities: set[str],
        evidence_list: list[Evidence],
    ) -> float:
        """Weighted Jaccard similarity between pattern requirements and evidence."""
        req_types = set(pattern.required_evidence_types)
        req_sources = set(pattern.required_sources)

        type_intersection = len(req_types & evidence_types)
        type_union = len(req_types | evidence_types)
        type_jaccard = type_intersection / type_union if type_union > 0 else 0.0

        src_intersection = len(req_sources & sources)
        src_union = len(req_sources | sources)
        src_jaccard = src_intersection / src_union if src_union > 0 else 0.0

        severity_match = 1.0 if pattern.typical_severity in severities else 0.3

        return type_jaccard * 0.5 + src_jaccard * 0.3 + severity_match * 0.2

    @staticmethod
    def _explain(pattern: FailurePattern, score: float, missing: list[str]) -> str:
        parts = [f"Pattern '{pattern.name}' matched with similarity {score:.2f}."]
        if missing:
            parts.append(f"Missing evidence types: {', '.join(missing)}.")
        else:
            parts.append("All required evidence types present.")
        parts.append(f"Historical matches: {pattern.historical_matches}. Prior: {pattern.prior_probability:.3f}.")
        return " ".join(parts)
