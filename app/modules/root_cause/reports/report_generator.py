"""report_generator.py — Investigation Report Generator."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Investigation, InvestigationReport, InvestigationSummary,
    Evidence, TimelineSequence, CausalChain, Hypothesis,
    PrimaryCause, SecondaryCause, ContributingFactor,
    Recommendation, CorrectiveAction, PreventiveAction,
    ReportFormat, InvestigationMemory, PatternMatch,
    BayesianConfidenceReport, CounterfactualScenario,
)

log = get_logger("root_cause.reports")


class ReportGenerator:
    """Generates structured investigation reports in multiple formats."""

    def generate_report(
        self,
        investigation: Investigation,
        evidence_list: list[Evidence],
        timeline: TimelineSequence | None,
        causal_chain: CausalChain | None,
        hypotheses: list[Hypothesis],
        primary_cause: PrimaryCause | None,
        secondary_causes: list[SecondaryCause],
        contributing_factors: list[ContributingFactor],
        recommendations: list[Recommendation],
        corrective_actions: list[CorrectiveAction],
        preventive_actions: list[PreventiveAction],
        graphrag_citations: list[str],
        kg_paths: list[list[str]],
    ) -> InvestigationReport:
        log.info(f"Generating report for investigation {investigation.id}")
        summary = InvestigationSummary(
            investigation_id=investigation.id,
            incident_id=investigation.incident_id,
            status=investigation.status,
            primary_cause=primary_cause,
            secondary_causes=secondary_causes,
            contributing_factors=contributing_factors,
            total_evidence_count=len(evidence_list),
            total_hypotheses=len(hypotheses),
            overall_confidence=investigation.overall_confidence,
            duration_seconds=investigation.duration_seconds,
            recommendations_count=len(recommendations),
        )
        rejected = [
            {"title": h.title, "reason": h.rejection_reason or "Outranked"}
            for h in hypotheses if h.status.value == "REJECTED"
        ]
        lessons = self.extract_lessons_learned_from_data(
            primary_cause, contributing_factors, recommendations,
        )
        return InvestigationReport(
            investigation_id=investigation.id,
            title=f"RCA Report — {investigation.title}",
            summary=summary,
            evidence_list=evidence_list,
            timeline=timeline,
            causal_graph=causal_chain,
            hypotheses=hypotheses,
            primary_cause=primary_cause,
            secondary_causes=secondary_causes,
            contributing_factors=contributing_factors,
            recommendations=recommendations,
            corrective_actions=corrective_actions,
            preventive_actions=preventive_actions,
            graphrag_citations=graphrag_citations,
            knowledge_graph_paths=kg_paths,
            confidence_explanation=f"Overall confidence: {investigation.overall_confidence:.3f}",
            alternative_hypotheses_rejected=rejected,
            lessons_learned=lessons,
            format=ReportFormat.JSON,
        )

    def generate_executive_summary(self, report: InvestigationReport) -> str:
        lines = [
            f"# Executive Summary — {report.title}",
            f"**Investigation ID**: {report.investigation_id}",
            f"**Status**: {report.summary.status.value}",
            f"**Overall Confidence**: {report.summary.overall_confidence:.1%}",
            f"**Duration**: {report.summary.duration_seconds:.1f}s",
            f"**Evidence Items**: {report.summary.total_evidence_count}",
            f"**Hypotheses Evaluated**: {report.summary.total_hypotheses}",
            f"**Recommendations**: {report.summary.recommendations_count}",
        ]
        if report.primary_cause:
            lines.append(f"\n## Root Cause\n{report.primary_cause.description}")
            lines.append(f"Confidence: {report.primary_cause.confidence:.1%}")
        if report.contributing_factors:
            lines.append("\n## Contributing Factors")
            for cf in report.contributing_factors:
                lines.append(f"- {cf.description} (confidence: {cf.confidence:.1%})")
        return "\n".join(lines)

    def generate_markdown_report(self, report: InvestigationReport) -> str:
        sections = [self.generate_executive_summary(report)]
        # Timeline
        if report.timeline and report.timeline.events:
            sections.append("\n## Investigation Timeline")
            for evt in report.timeline.events:
                marker = " ⚠" if evt.is_anomalous else ""
                sections.append(f"- **{evt.timestamp}** [{evt.severity}]{marker} {evt.title}")
        # Causal Graph
        if report.causal_graph and report.causal_graph.nodes:
            sections.append("\n## Causal Graph")
            for node in report.causal_graph.nodes:
                tag = " [ROOT CAUSE]" if node.is_root_cause else ""
                sections.append(f"- {node.label}{tag} (confidence: {node.confidence:.2f})")
        # Evidence
        sections.append("\n## Evidence Summary")
        for ev in report.evidence_list:
            sections.append(f"- [{ev.source.value}] {ev.title} — confidence {ev.confidence:.2f}")
        # Recommendations
        sections.append("\n## Recommendations")
        for rec in report.recommendations:
            sections.append(f"- **[{rec.priority.value}]** {rec.title}: {rec.description}")
        # Corrective
        if report.corrective_actions:
            sections.append("\n## Corrective Actions")
            for ca in report.corrective_actions:
                sections.append(f"- {ca.title}: {ca.corrective_measure}")
        # Preventive
        if report.preventive_actions:
            sections.append("\n## Preventive Actions")
            for pa in report.preventive_actions:
                sections.append(f"- {pa.title}: {pa.prevention_strategy}")
        # Lessons
        if report.lessons_learned:
            sections.append("\n## Lessons Learned")
            for lesson in report.lessons_learned:
                sections.append(f"- {lesson}")
        return "\n".join(sections)

    def generate_json_report(self, report: InvestigationReport) -> dict:
        return report.model_dump(mode="json")

    def extract_lessons_learned(self, report: InvestigationReport) -> list[str]:
        return self.extract_lessons_learned_from_data(
            report.primary_cause, report.contributing_factors, report.recommendations,
        )

    @staticmethod
    def extract_lessons_learned_from_data(
        primary_cause: PrimaryCause | None,
        contributing_factors: list[ContributingFactor],
        recommendations: list[Recommendation],
    ) -> list[str]:
        lessons: list[str] = []
        if primary_cause:
            lessons.append(f"Primary root cause identified: {primary_cause.description}")
        for cf in contributing_factors:
            if cf.mitigation:
                lessons.append(f"Contributing factor '{cf.description}' can be mitigated by: {cf.mitigation}")
        critical = [r for r in recommendations if r.priority.value == "CRITICAL"]
        if critical:
            lessons.append(f"{len(critical)} critical recommendation(s) require immediate attention")
        return lessons

    def generate_extended_report(
        self,
        base_report: InvestigationReport,
        memory: InvestigationMemory | None = None,
        pattern_matches: list[PatternMatch] | None = None,
        bayesian_report: BayesianConfidenceReport | None = None,
        counterfactual_scenarios: list[CounterfactualScenario] | None = None,
        similar_incidents: list[dict] | None = None
    ) -> dict:
        extended_data = base_report.model_dump(mode="json")
        
        if memory:
            extended_data["memory"] = memory.model_dump(mode="json")
        if pattern_matches:
            extended_data["pattern_matches"] = [pm.model_dump(mode="json") for pm in pattern_matches]
        if bayesian_report:
            extended_data["bayesian_confidence"] = bayesian_report.model_dump(mode="json")
        if counterfactual_scenarios:
            extended_data["counterfactual_scenarios"] = [cs.model_dump(mode="json") for cs in counterfactual_scenarios]
        if similar_incidents:
            extended_data["similar_incidents"] = similar_incidents
            
        return extended_data

    def format_counterfactual_section(self, scenarios: list[CounterfactualScenario]) -> str:
        sections = ["\n## Counterfactual Scenarios"]
        for s in scenarios:
            sections.append(f"- **{s.title}**: {s.description}")
        return "\n".join(sections)

    def format_pattern_match_section(self, matches: list[PatternMatch]) -> str:
        sections = ["\n## Pattern Matches"]
        for pm in matches:
            sections.append(f"- Matched Pattern ID: {pm.pattern_id} (Similarity: {pm.similarity_score:.2f})")
        return "\n".join(sections)

    def format_bayesian_section(self, report: BayesianConfidenceReport) -> str:
        sections = [
            "\n## Bayesian Confidence Analysis",
            f"**Overall System Confidence**: {report.overall_confidence:.2f}"
        ]
        return "\n".join(sections)

    def format_lessons_section(self, lessons: list[str]) -> str:
        sections = ["\n## Lessons Learned"]
        for lesson in lessons:
            sections.append(f"- {lesson}")
        return "\n".join(sections)

