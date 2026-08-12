"""investigation_memory.py — Domain service for building investigation memory entries."""
from __future__ import annotations
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Investigation, InvestigationReport, InvestigationMemory,
    LessonLearned, EvidenceFingerprint,
)
from app.modules.root_cause.memory.memory_index import build_fingerprint

log = get_logger("root_cause.memory.builder")


class InvestigationMemoryBuilder:
    """Converts a completed Investigation + Report into an InvestigationMemory entry."""

    def build(
        self,
        investigation: Investigation,
        report: InvestigationReport,
    ) -> InvestigationMemory:
        log.info(f"Building memory for investigation {investigation.id}")
        fingerprint = build_fingerprint(report.evidence_list)
        root_cause_desc = (
            investigation.primary_cause.description
            if investigation.primary_cause
            else "Root cause not identified"
        )
        lessons = report.lessons_learned or []
        matched_patterns: list[str] = report.metadata.get("matched_pattern_ids", [])
        return InvestigationMemory(
            investigation_id=investigation.id,
            incident_id=investigation.incident_id,
            title=investigation.title,
            root_cause_description=root_cause_desc,
            overall_confidence=investigation.overall_confidence,
            duration_seconds=investigation.duration_seconds,
            status=investigation.status,
            zone_ids=[investigation.zone_id] if investigation.zone_id else [],
            equipment_ids=investigation.equipment_ids,
            worker_ids=investigation.worker_ids,
            matched_pattern_ids=matched_patterns,
            recommendation_count=len(report.recommendations),
            evidence_count=len(report.evidence_list),
            hypothesis_count=len(report.hypotheses),
            fingerprint=fingerprint,
            lessons_learned=lessons,
            graphrag_citations=report.graphrag_citations,
            kg_node_ids=report.knowledge_graph_paths[0] if report.knowledge_graph_paths else [],
            completed_at=investigation.completed_at or datetime.now(timezone.utc).isoformat(),
        )

    def extract_lessons(
        self,
        investigation: Investigation,
        report: InvestigationReport,
    ) -> list[LessonLearned]:
        """Extract structured lessons from a completed investigation report."""
        lessons: list[LessonLearned] = []
        zones = [investigation.zone_id] if investigation.zone_id else []
        equip_types = ["EQUIPMENT"]  # Generalised; production would use KG entity type lookup

        # Primary cause lesson
        if investigation.primary_cause:
            lessons.append(LessonLearned(
                investigation_id=investigation.id,
                lesson_text=f"Root cause confirmed: {investigation.primary_cause.description}. "
                            f"Confidence: {investigation.primary_cause.confidence:.1%}.",
                lesson_category="ROOT_CAUSE",
                applies_to_zones=zones,
                applies_to_equipment_types=equip_types,
                confidence=investigation.primary_cause.confidence,
                tags=["root_cause", investigation.incident_id],
            ))

        # Contributing factor lessons
        for cf in investigation.contributing_factors:
            lessons.append(LessonLearned(
                investigation_id=investigation.id,
                lesson_text=f"Contributing factor: {cf.description}. Mitigation: {cf.mitigation or 'Review required'}.",
                lesson_category="CONTRIBUTING_FACTOR",
                applies_to_zones=zones,
                applies_to_equipment_types=equip_types,
                confidence=cf.confidence,
                tags=["contributing_factor"],
            ))

        # Recommendation-based lessons
        for rec in report.recommendations[:3]:  # Top 3 recommendations
            lessons.append(LessonLearned(
                investigation_id=investigation.id,
                lesson_text=f"Recommended action [{rec.priority.value}]: {rec.title} — {rec.description}",
                lesson_category="RECOMMENDATION",
                applies_to_zones=zones,
                applies_to_equipment_types=equip_types,
                confidence=0.7,
                tags=["recommendation", rec.recommendation_type.value],
            ))

        return lessons
