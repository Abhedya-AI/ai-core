"""investigation_service.py — RCA Investigation Orchestrator.

Coordinates the full investigation pipeline:
1. Evidence collection from all platform modules
2. Timeline construction and correlation
3. Causal graph building
4. Hypothesis generation and ranking
5. Root cause identification
6. Recommendation generation
7. Confidence computation
8. Report generation and Knowledge Graph sync
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.modules.root_cause.domain.models import (
    Investigation, InvestigationStatus, InvestigationReport, InvestigationSummary,
    Evidence, PrimaryCause, SecondaryCause, ContributingFactor,
    Recommendation, CorrectiveAction, PreventiveAction,
    CausalChain, Hypothesis, TimelineSequence,
)
from app.modules.root_cause.events.rca_events import (
    publish_rca_event, RCATopics,
    InvestigationStarted, EvidenceCollected, TimelineCompleted,
    HypothesisGenerated, RootCauseIdentified, RecommendationGenerated,
    InvestigationCompleted,
)
from app.modules.root_cause.evidence.evidence_collector import EvidenceCollectionEngine
from app.modules.root_cause.evidence.confidence_engine import ConfidenceEngine
from app.modules.root_cause.timeline.timeline_engine import TimelineEngine
from app.modules.root_cause.causal_graph.causal_graph_engine import CausalGraphEngine
from app.modules.root_cause.hypothesis.hypothesis_engine import HypothesisEngine
from app.modules.root_cause.recommendation.recommendation_engine import RecommendationEngine
from app.modules.root_cause.reports.report_generator import ReportGenerator

log = get_logger("root_cause.investigation")


class InvestigationService:
    """Orchestrates end-to-end Root Cause Analysis investigations."""

    def __init__(
        self,
        evidence_engine: EvidenceCollectionEngine | None = None,
        timeline_engine: TimelineEngine | None = None,
        causal_engine: CausalGraphEngine | None = None,
        hypothesis_engine: HypothesisEngine | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        confidence_engine: ConfidenceEngine | None = None,
        report_generator: ReportGenerator | None = None,
    ) -> None:
        self.evidence_engine = evidence_engine or EvidenceCollectionEngine()
        self.timeline_engine = timeline_engine or TimelineEngine()
        self.causal_engine = causal_engine or CausalGraphEngine()
        self.hypothesis_engine = hypothesis_engine or HypothesisEngine()
        self.recommendation_engine = recommendation_engine or RecommendationEngine()
        self.confidence_engine = confidence_engine or ConfidenceEngine()
        self.report_generator = report_generator or ReportGenerator()
        # In-memory store for investigations (production would use PostgreSQL)
        self._investigations: dict[str, Investigation] = {}
        self._evidence_store: dict[str, list[Evidence]] = {}
        self._timeline_store: dict[str, TimelineSequence] = {}
        self._causal_store: dict[str, CausalChain] = {}
        self._hypothesis_store: dict[str, list[Hypothesis]] = {}
        self._recommendation_store: dict[str, list[Recommendation]] = {}
        self._report_store: dict[str, InvestigationReport] = {}

    async def start_investigation(
        self,
        incident_id: str,
        title: str,
        zone_id: str | None = None,
        equipment_ids: list[str] | None = None,
        worker_ids: list[str] | None = None,
        triggered_by: str = "system",
    ) -> Investigation:
        investigation = Investigation(
            incident_id=incident_id,
            title=title,
            zone_id=zone_id,
            equipment_ids=equipment_ids or [],
            worker_ids=worker_ids or [],
            triggered_by=triggered_by,
            status=InvestigationStatus.INITIATED,
        )
        self._investigations[investigation.id] = investigation
        log.info(f"Investigation {investigation.id} started for incident {incident_id}")
        await publish_rca_event(
            InvestigationStarted(
                investigation_id=investigation.id,
                incident_id=incident_id,
                triggered_by=triggered_by,
            ),
            RCATopics.INVESTIGATION_STARTED,
        )
        return investigation

    async def run_investigation(self, investigation: Investigation) -> Investigation:
        log.info(f"Running full investigation pipeline for {investigation.id}")
        start_time = datetime.now(timezone.utc)

        # Phase 1: Evidence Collection
        investigation.status = InvestigationStatus.EVIDENCE_COLLECTION
        evidence_list = await self.evidence_engine.collect_all_evidence(
            incident_id=investigation.incident_id,
            zone_id=investigation.zone_id or "unknown",
            time_window_seconds=3600,
        )
        self._evidence_store[investigation.id] = evidence_list
        investigation.evidence_ids = [e.id for e in evidence_list]
        await publish_rca_event(
            EvidenceCollected(
                investigation_id=investigation.id,
                evidence_count=len(evidence_list),
                sources=list({e.source.value for e in evidence_list}),
            ),
            RCATopics.EVIDENCE_COLLECTED,
        )

        # Phase 2: Timeline Construction
        investigation.status = InvestigationStatus.TIMELINE_CONSTRUCTION
        timeline = self.timeline_engine.construct_timeline(evidence_list, investigation.id)
        timeline = self.timeline_engine.correlate_events(timeline, correlation_window_seconds=60.0)
        self._timeline_store[investigation.id] = timeline
        await publish_rca_event(
            TimelineCompleted(
                investigation_id=investigation.id,
                event_count=len(timeline.events),
                duration_seconds=timeline.duration_seconds,
            ),
            RCATopics.TIMELINE_COMPLETED,
        )

        # Phase 3: Causal Graph
        investigation.status = InvestigationStatus.HYPOTHESIS_GENERATION
        causal_chain = self.causal_engine.build_causal_graph(
            investigation.id, evidence_list, investigation.incident_id,
        )
        self._causal_store[investigation.id] = causal_chain

        # Phase 4: Hypothesis Generation
        hypotheses = self.hypothesis_engine.generate_hypotheses(
            evidence_list, causal_chain, investigation.id,
        )
        hypotheses = self.hypothesis_engine.rank_hypotheses(hypotheses)
        self._hypothesis_store[investigation.id] = hypotheses
        investigation.hypothesis_ids = [h.id for h in hypotheses]
        top_title = hypotheses[0].title if hypotheses else "None"
        await publish_rca_event(
            HypothesisGenerated(
                investigation_id=investigation.id,
                hypothesis_count=len(hypotheses),
                top_hypothesis=top_title,
            ),
            RCATopics.HYPOTHESIS_GENERATED,
        )

        # Phase 5: Root Cause Identification
        investigation.status = InvestigationStatus.ROOT_CAUSE_ANALYSIS
        primary_cause = self.hypothesis_engine.find_primary_cause(hypotheses)
        investigation.primary_cause = primary_cause
        contributing_factors = self.hypothesis_engine.find_contributing_factors(
            hypotheses, evidence_list,
        )
        investigation.contributing_factors = contributing_factors
        if primary_cause:
            await publish_rca_event(
                RootCauseIdentified(
                    investigation_id=investigation.id,
                    primary_cause_description=primary_cause.description,
                    confidence=primary_cause.confidence,
                ),
                RCATopics.ROOT_CAUSE_IDENTIFIED,
            )

        # Phase 6: Recommendations
        investigation.status = InvestigationStatus.RECOMMENDATION_GENERATION
        recommendations = self.recommendation_engine.generate_recommendations(
            investigation, primary_cause, contributing_factors, evidence_list,
        )
        recommendations = self.recommendation_engine.prioritize_recommendations(recommendations)
        self._recommendation_store[investigation.id] = recommendations
        investigation.recommendation_ids = [r.id for r in recommendations]
        critical_count = sum(1 for r in recommendations if r.priority.value == "CRITICAL")
        await publish_rca_event(
            RecommendationGenerated(
                investigation_id=investigation.id,
                recommendation_count=len(recommendations),
                critical_count=critical_count,
            ),
            RCATopics.RECOMMENDATION_GENERATED,
        )

        # Phase 7: Confidence
        hyp_scores = [h.score.overall_confidence for h in hypotheses]
        investigation.overall_confidence = self.confidence_engine.compute_investigation_confidence(
            evidence_list, hyp_scores,
        )

        # Duration
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        investigation.duration_seconds = elapsed
        investigation.status = InvestigationStatus.REVIEW
        self._investigations[investigation.id] = investigation
        log.info(f"Investigation {investigation.id} pipeline complete in {elapsed:.1f}s")
        return investigation

    async def complete_investigation(self, investigation: Investigation) -> InvestigationReport:
        log.info(f"Completing investigation {investigation.id}")
        evidence_list = self._evidence_store.get(investigation.id, [])
        timeline = self._timeline_store.get(investigation.id)
        causal_chain = self._causal_store.get(investigation.id)
        hypotheses = self._hypothesis_store.get(investigation.id, [])
        recommendations = self._recommendation_store.get(investigation.id, [])

        corrective = [r for r in recommendations if isinstance(r, CorrectiveAction)]
        preventive = [r for r in recommendations if isinstance(r, PreventiveAction)]

        report = self.report_generator.generate_report(
            investigation=investigation,
            evidence_list=evidence_list,
            timeline=timeline,
            causal_chain=causal_chain,
            hypotheses=hypotheses,
            primary_cause=investigation.primary_cause,
            secondary_causes=investigation.secondary_causes,
            contributing_factors=investigation.contributing_factors,
            recommendations=recommendations,
            corrective_actions=corrective,
            preventive_actions=preventive,
            graphrag_citations=[],
            kg_paths=[],
        )
        self._report_store[investigation.id] = report

        investigation.status = InvestigationStatus.COMPLETED
        investigation.completed_at = datetime.now(timezone.utc).isoformat()
        self._investigations[investigation.id] = investigation

        await publish_rca_event(
            InvestigationCompleted(
                investigation_id=investigation.id,
                incident_id=investigation.incident_id,
                overall_confidence=investigation.overall_confidence,
                duration_seconds=investigation.duration_seconds,
            ),
            RCATopics.INVESTIGATION_COMPLETED,
        )
        return report

    async def get_investigation(self, investigation_id: str) -> Investigation | None:
        return self._investigations.get(investigation_id)

    async def list_investigations(
        self, status: str | None = None, limit: int = 50, offset: int = 0,
    ) -> list[Investigation]:
        items = list(self._investigations.values())
        if status:
            items = [i for i in items if i.status.value == status]
        return items[offset : offset + limit]

    async def search_investigations(self, query: str) -> list[Investigation]:
        q = query.lower()
        return [
            inv for inv in self._investigations.values()
            if q in inv.title.lower() or q in inv.description.lower()
        ]

    def get_evidence(self, investigation_id: str) -> list[Evidence]:
        return self._evidence_store.get(investigation_id, [])

    def get_timeline(self, investigation_id: str) -> TimelineSequence | None:
        return self._timeline_store.get(investigation_id)

    def get_causal_chain(self, investigation_id: str) -> CausalChain | None:
        return self._causal_store.get(investigation_id)

    def get_hypotheses(self, investigation_id: str) -> list[Hypothesis]:
        return self._hypothesis_store.get(investigation_id, [])

    def get_recommendations(self, investigation_id: str) -> list[Recommendation]:
        return self._recommendation_store.get(investigation_id, [])

    def get_report(self, investigation_id: str) -> InvestigationReport | None:
        return self._report_store.get(investigation_id)
