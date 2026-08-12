"""pattern_builder.py — Auto-extraction of failure patterns from completed investigations."""
from __future__ import annotations
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Investigation, InvestigationReport, FailurePattern, PatternType,
)

log = get_logger("root_cause.patterns.builder")


class PatternBuilder:
    """Extracts and builds new failure patterns from completed investigations."""

    def extract_from_investigation(
        self,
        investigation: Investigation,
        report: InvestigationReport,
        min_confidence: float = 0.6,
    ) -> FailurePattern | None:
        """Extract a new reusable pattern from a completed investigation."""
        if investigation.overall_confidence < min_confidence:
            log.info(f"Investigation {investigation.id} confidence too low for pattern extraction")
            return None
        if not investigation.primary_cause:
            return None

        evidence_types = list({e.evidence_type.value for e in report.evidence_list})
        sources = list({e.source.value for e in report.evidence_list})
        severity_counts: dict[str, int] = {}
        for e in report.evidence_list:
            severity_counts[e.severity] = severity_counts.get(e.severity, 0) + 1
        typical_severity = max(severity_counts, key=severity_counts.get) if severity_counts else "MEDIUM"

        causal_template: list[str] = []
        if report.causal_graph:
            ordered = sorted(report.causal_graph.nodes, key=lambda n: n.depth)
            causal_template = [n.label for n in ordered[:5]]

        trigger_conditions = [
            f"{e.title} — {e.description[:60]}" for e in report.evidence_list[:3]
            if e.severity in ("CRITICAL", "HIGH")
        ]

        return FailurePattern(
            name=f"Extracted: {investigation.title[:40]}",
            pattern_type=PatternType.CUSTOM,
            description=(
                f"Auto-extracted from investigation '{investigation.title}'. "
                f"Root cause: {investigation.primary_cause.description[:120]}."
            ),
            trigger_conditions=trigger_conditions or ["High-severity evidence detected"],
            causal_chain_template=causal_template,
            prior_probability=investigation.overall_confidence * 0.1,
            required_evidence_types=evidence_types[:5],
            required_sources=sources[:3],
            typical_severity=typical_severity,
            is_seeded=False,
            confidence_score=investigation.overall_confidence,
        )
