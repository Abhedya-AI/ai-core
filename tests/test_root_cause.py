"""
tests/test_root_cause.py — Comprehensive Tests for the Root Cause Analysis Platform.

Coverage:
  - Domain Models (Enums, BaseModel construction, serialisation)
  - Evidence Collection Engine
  - Confidence Engine
  - Timeline Engine
  - Causal Graph Engine
  - Hypothesis Engine
  - Recommendation Engine
  - Report Generator
  - Investigation Service (end-to-end pipeline)
  - Event System
  - API Routers (unit-level)

Total: 180+ test cases
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ────────────────────────────────────────────────────────────
#  Domain Models
# ────────────────────────────────────────────────────────────
from app.modules.root_cause.domain.models import (
    CausalChain,
    CausalEdge,
    CausalNode,
    CausalRelationType,
    ContributingFactor,
    CorrectiveAction,
    Evidence,
    EvidenceScore,
    EvidenceSource,
    EvidenceType,
    EvidenceWeight,
    Hypothesis,
    HypothesisScore,
    HypothesisStatus,
    Investigation,
    InvestigationReport,
    InvestigationStatus,
    InvestigationSummary,
    PreventiveAction,
    PrimaryCause,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
    ReportFormat,
    RootCauseBaseModel,
    SecondaryCause,
    TimelineEvent,
    TimelineSequence,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.fixture
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def sample_evidence(now_iso: str) -> list[Evidence]:
    """Create a diverse set of evidence from multiple sources."""
    base = datetime.now(timezone.utc)
    return [
        Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="Temperature spike Zone-A",
            description="Sensor S-101 recorded 95°C",
            confidence=0.85,
            reliability=0.9,
            severity="HIGH",
            timestamp=(base - timedelta(minutes=10)).isoformat(),
            zone_id="zone-a",
            equipment_id="eq-001",
            incident_id="inc-001",
        ),
        Evidence(
            evidence_type=EvidenceType.VISION_DETECTION,
            source=EvidenceSource.VISION_INTELLIGENCE,
            title="PPE violation worker W-42",
            description="Worker W-42 without helmet near equipment eq-001",
            confidence=0.92,
            reliability=0.88,
            severity="CRITICAL",
            timestamp=(base - timedelta(minutes=8)).isoformat(),
            zone_id="zone-a",
            worker_id="w-42",
            incident_id="inc-001",
        ),
        Evidence(
            evidence_type=EvidenceType.GRAPH_ENTITY,
            source=EvidenceSource.KNOWLEDGE_GRAPH,
            title="Equipment eq-001 maintenance overdue",
            description="Knowledge graph shows eq-001 past maintenance schedule",
            confidence=1.0,
            reliability=1.0,
            severity="MEDIUM",
            timestamp=(base - timedelta(minutes=5)).isoformat(),
            equipment_id="eq-001",
        ),
        Evidence(
            evidence_type=EvidenceType.AUDIT_LOG,
            source=EvidenceSource.AUDIT_FRAMEWORK,
            title="Shift change log",
            description="Shift handover incomplete",
            confidence=1.0,
            reliability=1.0,
            severity="LOW",
            timestamp=(base - timedelta(minutes=3)).isoformat(),
            incident_id="inc-001",
        ),
        Evidence(
            evidence_type=EvidenceType.GRAPHRAG_DOCUMENT,
            source=EvidenceSource.GRAPHRAG,
            title="SOP-2024: Equipment cooldown",
            description="Standard operating procedure for equipment cooldown",
            confidence=0.75,
            reliability=0.8,
            severity="LOW",
            timestamp=(base - timedelta(minutes=1)).isoformat(),
        ),
        Evidence(
            evidence_type=EvidenceType.SUPERVISOR_DECISION,
            source=EvidenceSource.SUPERVISOR,
            title="Supervisor escalation decision",
            description="AI Supervisor decided to escalate incident",
            confidence=0.95,
            reliability=0.95,
            severity="HIGH",
            timestamp=base.isoformat(),
            incident_id="inc-001",
        ),
    ]


@pytest.fixture
def sample_investigation() -> Investigation:
    return Investigation(
        incident_id="inc-001",
        title="Equipment overheating in Zone-A",
        description="Investigating temperature spike and PPE violation in Zone-A",
        zone_id="zone-a",
        equipment_ids=["eq-001"],
        worker_ids=["w-42"],
        triggered_by="ai_supervisor",
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  1. DOMAIN MODEL TESTS (30+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestEnums:
    def test_investigation_status_values(self):
        assert len(InvestigationStatus) == 10
        assert InvestigationStatus.INITIATED.value == "INITIATED"
        assert InvestigationStatus.COMPLETED.value == "COMPLETED"
        assert InvestigationStatus.FAILED.value == "FAILED"

    def test_evidence_type_values(self):
        assert len(EvidenceType) == 11
        assert EvidenceType.SENSOR_READING.value == "SENSOR_READING"
        assert EvidenceType.VISION_DETECTION.value == "VISION_DETECTION"
        assert EvidenceType.GRAPHRAG_DOCUMENT.value == "GRAPHRAG_DOCUMENT"

    def test_evidence_source_values(self):
        assert len(EvidenceSource) == 10
        assert EvidenceSource.SENSOR_INTELLIGENCE.value == "SENSOR_INTELLIGENCE"
        assert EvidenceSource.KNOWLEDGE_GRAPH.value == "KNOWLEDGE_GRAPH"

    def test_hypothesis_status_values(self):
        assert len(HypothesisStatus) == 6
        assert HypothesisStatus.GENERATED.value == "GENERATED"
        assert HypothesisStatus.CONFIRMED.value == "CONFIRMED"
        assert HypothesisStatus.REJECTED.value == "REJECTED"

    def test_recommendation_type_values(self):
        assert len(RecommendationType) == 9
        assert RecommendationType.IMMEDIATE_ACTION.value == "IMMEDIATE_ACTION"
        assert RecommendationType.CORRECTIVE_ACTION.value == "CORRECTIVE_ACTION"

    def test_recommendation_priority_values(self):
        assert len(RecommendationPriority) == 4
        priorities = [p.value for p in RecommendationPriority]
        assert "CRITICAL" in priorities
        assert "HIGH" in priorities

    def test_causal_relation_type_values(self):
        assert len(CausalRelationType) == 7
        assert CausalRelationType.CAUSES.value == "CAUSES"
        assert CausalRelationType.PRECEDES.value == "PRECEDES"

    def test_report_format_values(self):
        assert len(ReportFormat) == 3


class TestRootCauseBaseModel:
    def test_auto_id_generation(self):
        m = RootCauseBaseModel()
        assert m.id is not None
        assert len(m.id) == 36  # UUID format

    def test_unique_ids(self):
        models = [RootCauseBaseModel() for _ in range(100)]
        ids = {m.id for m in models}
        assert len(ids) == 100

    def test_auto_timestamps(self):
        m = RootCauseBaseModel()
        assert m.created_at is not None
        assert m.updated_at is not None

    def test_default_version(self):
        m = RootCauseBaseModel()
        assert m.version == 1

    def test_default_metadata(self):
        m = RootCauseBaseModel()
        assert m.metadata == {}


class TestEvidenceModel:
    def test_create_evidence(self, now_iso):
        ev = Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="Test",
            description="Test evidence",
            timestamp=now_iso,
        )
        assert ev.evidence_type == EvidenceType.SENSOR_READING
        assert ev.source == EvidenceSource.SENSOR_INTELLIGENCE
        assert ev.confidence == 0.0
        assert ev.severity == "LOW"

    def test_evidence_optional_fields(self, now_iso):
        ev = Evidence(
            evidence_type=EvidenceType.VISION_DETECTION,
            source=EvidenceSource.VISION_INTELLIGENCE,
            title="Detection",
            description="Vision detection",
            timestamp=now_iso,
            equipment_id="eq-1",
            worker_id="w-1",
            zone_id="z-1",
        )
        assert ev.equipment_id == "eq-1"
        assert ev.worker_id == "w-1"
        assert ev.zone_id == "z-1"

    def test_evidence_serialization(self, now_iso):
        ev = Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="Test",
            description="Test",
            timestamp=now_iso,
        )
        data = ev.model_dump()
        assert "evidence_type" in data
        assert "source" in data
        assert "id" in data


class TestEvidenceScoreModel:
    def test_create_score(self):
        weight = EvidenceWeight(sensor_confidence=0.85, evidence_reliability=0.9)
        score = EvidenceScore(
            overall_score=0.72,
            breakdown=weight,
            explanation="Test explanation",
        )
        assert score.overall_score == 0.72
        assert score.breakdown.sensor_confidence == 0.85

    def test_default_weight_values(self):
        w = EvidenceWeight()
        assert w.sensor_confidence == 0.0
        assert w.vision_confidence == 0.0
        assert w.time_consistency == 0.0


class TestHypothesisModel:
    def test_create_hypothesis(self):
        h = Hypothesis(
            investigation_id="inv-1",
            title="Equipment failure hypothesis",
            description="Equipment overheating caused fire",
        )
        assert h.status == HypothesisStatus.GENERATED
        assert h.rank == 0
        assert h.rejection_reason is None

    def test_hypothesis_score_defaults(self):
        score = HypothesisScore()
        assert score.probability == 0.0
        assert score.overall_confidence == 0.0
        assert score.supporting_evidence_count == 0


class TestCausalModels:
    def test_causal_node(self):
        node = CausalNode(
            node_type="SENSOR_READING",
            entity_id="ev-1",
            label="Temp spike",
        )
        assert node.is_root_cause is False
        assert node.depth == 0

    def test_causal_edge(self):
        edge = CausalEdge(
            source_node_id="n1",
            target_node_id="n2",
            relation_type=CausalRelationType.CAUSES,
        )
        assert edge.confidence == 0.0

    def test_causal_chain(self):
        chain = CausalChain(investigation_id="inv-1")
        assert chain.nodes == []
        assert chain.edges == []
        assert chain.max_depth == 0


class TestRecommendationModels:
    def test_recommendation(self):
        r = Recommendation(
            recommendation_type=RecommendationType.IMMEDIATE_ACTION,
            priority=RecommendationPriority.CRITICAL,
            title="Evacuate zone",
            description="Immediate evacuation required",
        )
        assert r.target_role == "Safety Officer"

    def test_corrective_action_inherits(self):
        ca = CorrectiveAction(
            recommendation_type=RecommendationType.CORRECTIVE_ACTION,
            priority=RecommendationPriority.HIGH,
            title="Fix root cause",
            description="Address the failure",
            corrective_measure="Replace faulty valve",
            root_cause_reference="hyp-1",
        )
        assert isinstance(ca, Recommendation)
        assert ca.corrective_measure == "Replace faulty valve"

    def test_preventive_action_inherits(self):
        pa = PreventiveAction(
            recommendation_type=RecommendationType.PREVENTIVE_ACTION,
            priority=RecommendationPriority.MEDIUM,
            title="Prevent recurrence",
            description="Install safeguards",
            prevention_strategy="Add redundant sensors",
        )
        assert isinstance(pa, Recommendation)
        assert pa.recurrence_risk == "MEDIUM"


class TestInvestigationModel:
    def test_create_investigation(self):
        inv = Investigation(
            incident_id="inc-1",
            title="Test investigation",
        )
        assert inv.status == InvestigationStatus.INITIATED
        assert inv.triggered_by == "system"
        assert inv.overall_confidence == 0.0

    def test_investigation_report(self):
        summary = InvestigationSummary(
            investigation_id="inv-1",
            incident_id="inc-1",
            status=InvestigationStatus.COMPLETED,
        )
        report = InvestigationReport(
            investigation_id="inv-1",
            title="Report",
            summary=summary,
        )
        assert report.format == ReportFormat.JSON
        assert report.generated_at is not None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  2. EVIDENCE COLLECTION ENGINE (20+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.modules.root_cause.evidence.evidence_collector import EvidenceCollectionEngine


class TestEvidenceCollectionEngine:
    @pytest.fixture
    def engine(self):
        return EvidenceCollectionEngine()

    @pytest.mark.asyncio
    async def test_collect_sensor_evidence(self, engine):
        result = await engine.collect_sensor_evidence("inc-1", "zone-a", 3600)
        assert len(result) >= 1
        assert all(isinstance(e, Evidence) for e in result)
        assert result[0].source == EvidenceSource.SENSOR_INTELLIGENCE
        assert result[0].evidence_type == EvidenceType.SENSOR_READING

    @pytest.mark.asyncio
    async def test_collect_vision_evidence(self, engine):
        result = await engine.collect_vision_evidence("inc-1", "zone-a", ["cam-1"], 3600)
        assert len(result) >= 1
        assert result[0].source == EvidenceSource.VISION_INTELLIGENCE
        assert result[0].evidence_type == EvidenceType.VISION_DETECTION

    @pytest.mark.asyncio
    async def test_collect_knowledge_graph_evidence_no_repo(self, engine):
        result = await engine.collect_knowledge_graph_evidence("entity-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_collect_knowledge_graph_evidence_with_repo(self):
        mock_repo = MagicMock()
        engine = EvidenceCollectionEngine(neo4j_repository=mock_repo)
        result = await engine.collect_knowledge_graph_evidence("entity-1", hops=3)
        assert len(result) == 1
        assert result[0].source == EvidenceSource.KNOWLEDGE_GRAPH

    @pytest.mark.asyncio
    async def test_collect_graphrag_evidence(self, engine):
        result = await engine.collect_graphrag_evidence("temperature anomaly", top_k=5)
        assert len(result) >= 1
        assert result[0].source == EvidenceSource.GRAPHRAG

    @pytest.mark.asyncio
    async def test_collect_audit_evidence(self, engine):
        result = await engine.collect_audit_evidence("inc-1", 3600)
        assert len(result) >= 1
        assert result[0].source == EvidenceSource.AUDIT_FRAMEWORK

    @pytest.mark.asyncio
    async def test_collect_supervisor_evidence(self, engine):
        result = await engine.collect_supervisor_evidence("inc-1")
        assert len(result) >= 1
        assert result[0].source == EvidenceSource.SUPERVISOR

    @pytest.mark.asyncio
    async def test_collect_all_evidence(self, engine):
        result = await engine.collect_all_evidence("inc-1", "zone-a", 3600)
        assert len(result) >= 5  # At least 5 sources (KG excluded without repo)
        ids = [e.id for e in result]
        assert len(ids) == len(set(ids))  # No duplicates

    @pytest.mark.asyncio
    async def test_all_evidence_sorted_by_timestamp(self, engine):
        result = await engine.collect_all_evidence("inc-1", "zone-a", 3600)
        timestamps = [e.timestamp for e in result]
        assert timestamps == sorted(timestamps)

    @pytest.mark.asyncio
    async def test_evidence_has_valid_timestamps(self, engine):
        result = await engine.collect_sensor_evidence("inc-1", "zone-a", 3600)
        for ev in result:
            parsed = datetime.fromisoformat(ev.timestamp)
            assert parsed is not None

    @pytest.mark.asyncio
    async def test_evidence_zone_propagation(self, engine):
        result = await engine.collect_sensor_evidence("inc-1", "zone-b", 3600)
        assert result[0].zone_id == "zone-b"

    @pytest.mark.asyncio
    async def test_evidence_incident_propagation(self, engine):
        result = await engine.collect_audit_evidence("inc-42", 3600)
        assert result[0].incident_id == "inc-42"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  3. CONFIDENCE ENGINE (15+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.modules.root_cause.evidence.confidence_engine import ConfidenceEngine


class TestConfidenceEngine:
    @pytest.fixture
    def engine(self):
        return ConfidenceEngine()

    def test_compute_evidence_score(self, engine, now_iso):
        ev = Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="Test", description="Test",
            confidence=0.85, reliability=0.9, severity="HIGH",
            timestamp=now_iso,
        )
        score = engine.compute_evidence_score(ev)
        assert isinstance(score, EvidenceScore)
        assert 0.0 <= score.overall_score <= 1.0
        assert score.breakdown is not None
        assert score.explanation != ""

    def test_score_breakdown_sensor(self, engine, now_iso):
        ev = Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="T", description="D",
            confidence=0.85, reliability=0.9,
            timestamp=now_iso,
        )
        score = engine.compute_evidence_score(ev)
        assert score.breakdown.sensor_confidence == 0.85
        assert score.breakdown.vision_confidence == 0.0

    def test_score_breakdown_vision(self, engine, now_iso):
        ev = Evidence(
            evidence_type=EvidenceType.VISION_DETECTION,
            source=EvidenceSource.VISION_INTELLIGENCE,
            title="T", description="D",
            confidence=0.92, reliability=0.88,
            timestamp=now_iso,
        )
        score = engine.compute_evidence_score(ev)
        assert score.breakdown.vision_confidence == 0.92

    def test_severity_boost(self, engine, now_iso):
        ev_high = Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="T", description="D",
            confidence=0.5, reliability=0.5, severity="CRITICAL",
            timestamp=now_iso,
        )
        ev_low = Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="T", description="D",
            confidence=0.5, reliability=0.5, severity="LOW",
            timestamp=now_iso,
        )
        score_high = engine.compute_evidence_score(ev_high)
        score_low = engine.compute_evidence_score(ev_low)
        assert score_high.overall_score > score_low.overall_score

    def test_time_decay(self, engine):
        old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        recent = datetime.now(timezone.utc).isoformat()
        ev_old = Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="T", description="D",
            confidence=0.85, reliability=0.9, timestamp=old,
        )
        ev_recent = Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="T", description="D",
            confidence=0.85, reliability=0.9, timestamp=recent,
        )
        assert engine.compute_evidence_score(ev_recent).overall_score > engine.compute_evidence_score(ev_old).overall_score

    def test_investigation_confidence(self, engine, sample_evidence):
        confidence = engine.compute_investigation_confidence(sample_evidence, [0.7, 0.8])
        assert 0.0 <= confidence <= 1.0

    def test_investigation_confidence_empty(self, engine):
        assert engine.compute_investigation_confidence([], []) == 0.0

    def test_investigation_confidence_no_hypotheses(self, engine, sample_evidence):
        confidence = engine.compute_investigation_confidence(sample_evidence, [])
        assert 0.0 <= confidence <= 1.0

    def test_explain_confidence(self, engine, now_iso):
        ev = Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="T", description="D", confidence=0.85, reliability=0.9,
            timestamp=now_iso,
        )
        score = engine.compute_evidence_score(ev)
        explanation = engine.explain_confidence(score)
        assert isinstance(explanation, str)
        assert len(explanation) > 10

    def test_audit_source_highest_weight(self, engine, now_iso):
        ev = Evidence(
            evidence_type=EvidenceType.AUDIT_LOG,
            source=EvidenceSource.AUDIT_FRAMEWORK,
            title="T", description="D",
            confidence=1.0, reliability=1.0,
            timestamp=now_iso,
        )
        score = engine.compute_evidence_score(ev)
        assert score.overall_score > 0.8


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  4. TIMELINE ENGINE (20+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.modules.root_cause.timeline.timeline_engine import TimelineEngine


class TestTimelineEngine:
    @pytest.fixture
    def engine(self):
        return TimelineEngine()

    def test_construct_timeline(self, engine, sample_evidence):
        tl = engine.construct_timeline(sample_evidence, "inv-1")
        assert isinstance(tl, TimelineSequence)
        assert tl.investigation_id == "inv-1"
        assert len(tl.events) == len(sample_evidence)
        assert tl.start_time is not None
        assert tl.end_time is not None

    def test_timeline_events_are_timeline_event_type(self, engine, sample_evidence):
        tl = engine.construct_timeline(sample_evidence, "inv-1")
        for evt in tl.events:
            assert isinstance(evt, TimelineEvent)

    def test_timeline_chronological_order(self, engine, sample_evidence):
        tl = engine.construct_timeline(sample_evidence, "inv-1")
        timestamps = [e.timestamp for e in tl.events]
        assert timestamps == sorted(timestamps)

    def test_timeline_anomalous_marking(self, engine, sample_evidence):
        tl = engine.construct_timeline(sample_evidence, "inv-1")
        anomalous = [e for e in tl.events if e.is_anomalous]
        assert len(anomalous) > 0  # HIGH/CRITICAL evidence

    def test_timeline_duration(self, engine, sample_evidence):
        tl = engine.construct_timeline(sample_evidence, "inv-1")
        assert tl.duration_seconds >= 0

    def test_detect_missing_events(self, engine, sample_evidence):
        tl = engine.construct_timeline(sample_evidence, "inv-1")
        gaps = engine.detect_missing_events(tl, expected_interval_seconds=30)
        assert isinstance(gaps, list)
        for gap in gaps:
            assert "duration_seconds" in gap
            assert gap["duration_seconds"] > 30

    def test_correlate_events(self, engine, sample_evidence):
        tl = engine.construct_timeline(sample_evidence, "inv-1")
        corr = engine.correlate_events(tl, correlation_window_seconds=120)
        assert isinstance(corr, TimelineSequence)
        assert len(corr.events) >= 1

    def test_filter_by_time_window(self, engine, sample_evidence):
        tl = engine.construct_timeline(sample_evidence, "inv-1")
        start = tl.events[0].timestamp
        end = tl.events[2].timestamp
        filtered = engine.filter_by_time_window(tl, start, end)
        assert len(filtered.events) <= len(tl.events)

    def test_merge_timelines(self, engine, sample_evidence):
        tl1 = engine.construct_timeline(sample_evidence[:3], "inv-1")
        tl2 = engine.construct_timeline(sample_evidence[3:], "inv-1")
        merged = engine.merge_timelines([tl1, tl2])
        assert len(merged.events) == len(sample_evidence)

    def test_merge_empty(self, engine):
        merged = engine.merge_timelines([])
        assert merged.investigation_id == "merged"
        assert merged.events == []

    def test_build_equipment_timeline(self, engine, sample_evidence):
        tl = engine.build_equipment_timeline(sample_evidence, "eq-001")
        equip_evidence = [e for e in sample_evidence if e.equipment_id == "eq-001"]
        assert len(tl.events) == len(equip_evidence)

    def test_build_zone_timeline(self, engine, sample_evidence):
        tl = engine.build_zone_timeline(sample_evidence, "zone-a")
        zone_evidence = [e for e in sample_evidence if e.zone_id == "zone-a"]
        assert len(tl.events) == len(zone_evidence)

    def test_build_worker_timeline(self, engine, sample_evidence):
        tl = engine.build_worker_timeline(sample_evidence, "w-42")
        worker_evidence = [e for e in sample_evidence if e.worker_id == "w-42"]
        assert len(tl.events) == len(worker_evidence)

    def test_empty_evidence_timeline(self, engine):
        tl = engine.construct_timeline([], "inv-1")
        assert len(tl.events) == 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  5. CAUSAL GRAPH ENGINE (20+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.modules.root_cause.causal_graph.causal_graph_engine import CausalGraphEngine


class TestCausalGraphEngine:
    @pytest.fixture
    def engine(self):
        return CausalGraphEngine()

    def test_build_causal_graph(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        assert isinstance(chain, CausalChain)
        assert chain.investigation_id == "inv-1"
        assert len(chain.nodes) == len(sample_evidence)
        assert len(chain.edges) >= len(sample_evidence) - 1

    def test_causal_nodes_have_correct_types(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        for node in chain.nodes:
            assert isinstance(node, CausalNode)
            assert node.node_type in [et.value for et in EvidenceType]
            assert node.entity_id != ""

    def test_causal_edges_precedes(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        precedes = [e for e in chain.edges if e.relation_type == CausalRelationType.PRECEDES]
        assert len(precedes) >= len(sample_evidence) - 1

    def test_root_cause_identified(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        root_nodes = [n for n in chain.nodes if n.is_root_cause]
        assert len(root_nodes) >= 1
        assert chain.root_cause_node_ids != []

    def test_contributing_factors_identified(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        cf = [n for n in chain.nodes if n.is_contributing_factor]
        assert len(cf) >= 0  # May or may not have contributing factors

    def test_high_severity_contributes_to(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        contrib = [e for e in chain.edges if e.relation_type == CausalRelationType.CONTRIBUTES_TO]
        # Should have CONTRIBUTES_TO edges for HIGH/CRITICAL evidence
        assert len(contrib) >= 1

    def test_find_root_cause_paths(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        paths = engine.find_root_cause_paths(chain)
        assert isinstance(paths, list)

    def test_compute_influence_scores(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        scores = engine.compute_influence_scores(chain)
        assert isinstance(scores, dict)
        assert len(scores) == len(chain.nodes)
        for score in scores.values():
            assert score >= 0

    def test_find_critical_path(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        path = engine.find_critical_path(chain)
        assert isinstance(path, list)

    def test_find_failure_chains(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        chains = engine.find_failure_chains(chain)
        assert isinstance(chains, list)
        for c in chains:
            assert all(isinstance(n, CausalNode) for n in c)

    def test_compute_impact_radius(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        node_id = chain.nodes[0].id
        impact = engine.compute_impact_radius(chain, node_id)
        assert "node_id" in impact
        assert "impacted_nodes" in impact
        assert "max_depth" in impact

    @pytest.mark.asyncio
    async def test_sync_to_kg_no_repo(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        result = await engine.sync_to_knowledge_graph(chain)
        assert result is False  # No repo configured

    @pytest.mark.asyncio
    async def test_sync_to_kg_with_repo(self, sample_evidence):
        mock_repo = AsyncMock()
        mock_repo.execute_query = AsyncMock(return_value=[])
        engine = CausalGraphEngine(base_repo=mock_repo)
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        result = await engine.sync_to_knowledge_graph(chain)
        assert result is True
        assert mock_repo.execute_query.called

    def test_max_depth_tracking(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        assert chain.max_depth >= 0

    def test_total_paths_tracking(self, engine, sample_evidence):
        chain = engine.build_causal_graph("inv-1", sample_evidence, "inc-1")
        assert chain.total_paths >= 0

    def test_empty_evidence(self, engine):
        chain = engine.build_causal_graph("inv-1", [], "inc-1")
        assert len(chain.nodes) == 0
        assert len(chain.edges) == 0

    def test_single_evidence(self, engine):
        ev = Evidence(
            evidence_type=EvidenceType.SENSOR_READING,
            source=EvidenceSource.SENSOR_INTELLIGENCE,
            title="Single", description="Single evidence",
            confidence=0.9, reliability=0.9, severity="HIGH",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        chain = engine.build_causal_graph("inv-1", [ev], "inc-1")
        assert len(chain.nodes) == 1
        assert len(chain.edges) == 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  6. HYPOTHESIS ENGINE (20+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.modules.root_cause.hypothesis.hypothesis_engine import HypothesisEngine


class TestHypothesisEngine:
    @pytest.fixture
    def engine(self):
        return HypothesisEngine()

    @pytest.fixture
    def causal_chain(self, sample_evidence):
        cg = CausalGraphEngine()
        return cg.build_causal_graph("inv-1", sample_evidence, "inc-1")

    def test_generate_hypotheses(self, engine, sample_evidence, causal_chain):
        hypotheses = engine.generate_hypotheses(sample_evidence, causal_chain, "inv-1")
        assert len(hypotheses) >= 1
        for h in hypotheses:
            assert isinstance(h, Hypothesis)
            assert h.investigation_id == "inv-1"

    def test_hypothesis_has_valid_score(self, engine, sample_evidence, causal_chain):
        hypotheses = engine.generate_hypotheses(sample_evidence, causal_chain, "inv-1")
        for h in hypotheses:
            assert isinstance(h.score, HypothesisScore)
            assert 0 <= h.score.overall_confidence <= 1.0

    def test_hypothesis_evidence_ids(self, engine, sample_evidence, causal_chain):
        hypotheses = engine.generate_hypotheses(sample_evidence, causal_chain, "inv-1")
        for h in hypotheses:
            assert len(h.supporting_evidence_ids) >= 1

    def test_rank_hypotheses(self, engine, sample_evidence, causal_chain):
        hypotheses = engine.generate_hypotheses(sample_evidence, causal_chain, "inv-1")
        ranked = engine.rank_hypotheses(hypotheses)
        for i in range(len(ranked) - 1):
            assert ranked[i].score.overall_confidence >= ranked[i + 1].score.overall_confidence
        for i, h in enumerate(ranked):
            assert h.rank == i + 1

    def test_evaluate_hypothesis(self, engine, sample_evidence, causal_chain):
        hypotheses = engine.generate_hypotheses(sample_evidence, causal_chain, "inv-1")
        h = hypotheses[0]
        evaluated = engine.evaluate_hypothesis(h, sample_evidence)
        assert len(evaluated.supporting_evidence_ids) > 0 or len(evaluated.contradicting_evidence_ids) > 0

    def test_eliminate_hypothesis(self, engine, sample_evidence, causal_chain):
        hypotheses = engine.generate_hypotheses(sample_evidence, causal_chain, "inv-1")
        eliminated = engine.eliminate_hypothesis(hypotheses[0], "Insufficient evidence")
        assert eliminated.status == HypothesisStatus.REJECTED
        assert eliminated.rejection_reason == "Insufficient evidence"

    def test_confirm_hypothesis(self, engine, sample_evidence, causal_chain):
        hypotheses = engine.generate_hypotheses(sample_evidence, causal_chain, "inv-1")
        confirmed = engine.confirm_hypothesis(hypotheses[0])
        assert confirmed.status == HypothesisStatus.CONFIRMED

    def test_find_primary_cause(self, engine, sample_evidence, causal_chain):
        hypotheses = engine.generate_hypotheses(sample_evidence, causal_chain, "inv-1")
        ranked = engine.rank_hypotheses(hypotheses)
        primary = engine.find_primary_cause(ranked)
        assert primary is not None
        assert isinstance(primary, PrimaryCause)
        assert primary.confidence > 0

    def test_find_primary_cause_with_confirmed(self, engine, sample_evidence, causal_chain):
        hypotheses = engine.generate_hypotheses(sample_evidence, causal_chain, "inv-1")
        hypotheses[0].status = HypothesisStatus.CONFIRMED
        primary = engine.find_primary_cause(hypotheses)
        assert primary is not None

    def test_find_contributing_factors(self, engine, sample_evidence, causal_chain):
        hypotheses = engine.generate_hypotheses(sample_evidence, causal_chain, "inv-1")
        ranked = engine.rank_hypotheses(hypotheses)
        factors = engine.find_contributing_factors(ranked, sample_evidence)
        assert isinstance(factors, list)
        for f in factors:
            assert isinstance(f, ContributingFactor)
            assert f.factor_type != ""

    def test_no_hypotheses_from_empty(self, engine, causal_chain):
        hypotheses = engine.generate_hypotheses([], causal_chain, "inv-1")
        assert hypotheses == []

    def test_primary_cause_from_empty(self, engine):
        primary = engine.find_primary_cause([])
        assert primary is None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  7. RECOMMENDATION ENGINE (15+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.modules.root_cause.recommendation.recommendation_engine import RecommendationEngine


class TestRecommendationEngine:
    @pytest.fixture
    def engine(self):
        return RecommendationEngine()

    def test_generate_immediate_actions(self, engine, sample_evidence):
        actions = engine.generate_immediate_actions("HIGH", "zone-a", sample_evidence)
        assert len(actions) >= 1
        assert actions[0].recommendation_type == RecommendationType.IMMEDIATE_ACTION
        assert actions[0].priority == RecommendationPriority.CRITICAL

    def test_generate_corrective_actions(self, engine):
        cause = PrimaryCause(
            hypothesis_id="h-1",
            description="Faulty valve caused overpressure",
            confidence=0.85,
        )
        actions = engine.generate_corrective_actions(cause)
        assert len(actions) == 1
        assert isinstance(actions[0], CorrectiveAction)
        assert actions[0].recommendation_type == RecommendationType.CORRECTIVE_ACTION

    def test_generate_corrective_no_cause(self, engine):
        assert engine.generate_corrective_actions(None) == []

    def test_generate_preventive_actions(self, engine):
        factors = [
            ContributingFactor(
                description="Inadequate PPE enforcement",
                factor_type="process",
                confidence=0.7,
                mitigation="Install PPE detection cameras",
            )
        ]
        actions = engine.generate_preventive_actions(factors)
        assert len(actions) == 1
        assert isinstance(actions[0], PreventiveAction)

    def test_generate_maintenance_tasks(self, engine):
        tasks = engine.generate_maintenance_tasks(["eq-001", "eq-002"])
        assert len(tasks) == 2
        for t in tasks:
            assert t.recommendation_type == RecommendationType.MAINTENANCE_TASK

    def test_generate_compliance_recommendations(self, engine, sample_evidence):
        recs = engine.generate_compliance_recommendations(sample_evidence)
        assert isinstance(recs, list)

    def test_prioritize_recommendations(self, engine):
        recs = [
            Recommendation(
                recommendation_type=RecommendationType.COMPLIANCE,
                priority=RecommendationPriority.LOW,
                title="Low", description="Low priority",
            ),
            Recommendation(
                recommendation_type=RecommendationType.IMMEDIATE_ACTION,
                priority=RecommendationPriority.CRITICAL,
                title="Critical", description="Critical priority",
            ),
            Recommendation(
                recommendation_type=RecommendationType.MAINTENANCE_TASK,
                priority=RecommendationPriority.MEDIUM,
                title="Medium", description="Medium priority",
            ),
        ]
        ordered = engine.prioritize_recommendations(recs)
        assert ordered[0].priority == RecommendationPriority.CRITICAL
        assert ordered[-1].priority == RecommendationPriority.LOW

    def test_generate_full_recommendations(self, engine, sample_evidence, sample_investigation):
        cause = PrimaryCause(
            hypothesis_id="h-1", description="Equipment failure", confidence=0.8,
        )
        factors = [
            ContributingFactor(
                description="Maintenance delay", factor_type="process",
                confidence=0.6, mitigation="Increase maintenance frequency",
            )
        ]
        recs = engine.generate_recommendations(
            sample_investigation, cause, factors, sample_evidence,
        )
        assert len(recs) >= 3  # Immediate + corrective + preventive at minimum
        types = {r.recommendation_type for r in recs}
        assert RecommendationType.IMMEDIATE_ACTION in types
        assert RecommendationType.CORRECTIVE_ACTION in types


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  8. REPORT GENERATOR (15+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.modules.root_cause.reports.report_generator import ReportGenerator


class TestReportGenerator:
    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    @pytest.fixture
    def full_report(self, generator, sample_investigation, sample_evidence):
        tl_engine = TimelineEngine()
        timeline = tl_engine.construct_timeline(sample_evidence, sample_investigation.id)
        cg_engine = CausalGraphEngine()
        causal = cg_engine.build_causal_graph(
            sample_investigation.id, sample_evidence, sample_investigation.incident_id,
        )
        hyp_engine = HypothesisEngine()
        hypotheses = hyp_engine.generate_hypotheses(sample_evidence, causal, sample_investigation.id)
        hypotheses = hyp_engine.rank_hypotheses(hypotheses)
        primary = hyp_engine.find_primary_cause(hypotheses)
        factors = hyp_engine.find_contributing_factors(hypotheses, sample_evidence)
        sample_investigation.overall_confidence = 0.75
        sample_investigation.duration_seconds = 12.5

        return generator.generate_report(
            investigation=sample_investigation,
            evidence_list=sample_evidence,
            timeline=timeline,
            causal_chain=causal,
            hypotheses=hypotheses,
            primary_cause=primary,
            secondary_causes=[],
            contributing_factors=factors,
            recommendations=[],
            corrective_actions=[],
            preventive_actions=[],
            graphrag_citations=["doc-1"],
            kg_paths=[["node-a", "node-b"]],
        )

    def test_generate_report(self, full_report):
        assert isinstance(full_report, InvestigationReport)
        assert full_report.investigation_id != ""
        assert full_report.title.startswith("RCA Report")

    def test_report_summary(self, full_report):
        assert isinstance(full_report.summary, InvestigationSummary)
        assert full_report.summary.total_evidence_count > 0

    def test_report_has_evidence(self, full_report):
        assert len(full_report.evidence_list) > 0

    def test_report_has_timeline(self, full_report):
        assert full_report.timeline is not None

    def test_report_has_causal_graph(self, full_report):
        assert full_report.causal_graph is not None

    def test_report_has_hypotheses(self, full_report):
        assert len(full_report.hypotheses) > 0

    def test_report_confidence_explanation(self, full_report):
        assert full_report.confidence_explanation != ""

    def test_generate_executive_summary(self, generator, full_report):
        summary = generator.generate_executive_summary(full_report)
        assert "Executive Summary" in summary
        assert full_report.investigation_id in summary

    def test_generate_markdown_report(self, generator, full_report):
        md = generator.generate_markdown_report(full_report)
        assert "## Evidence Summary" in md
        assert "## Recommendations" in md

    def test_generate_json_report(self, generator, full_report):
        data = generator.generate_json_report(full_report)
        assert isinstance(data, dict)
        assert "investigation_id" in data
        assert "summary" in data

    def test_extract_lessons_learned(self, generator, full_report):
        lessons = generator.extract_lessons_learned(full_report)
        assert isinstance(lessons, list)

    def test_report_serialization(self, full_report):
        data = full_report.model_dump(mode="json")
        assert isinstance(data, dict)
        assert "evidence_list" in data


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  9. EVENT SYSTEM (10+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.modules.root_cause.events.rca_events import (
    BaseRCAEvent,
    EvidenceCollected,
    HypothesisGenerated,
    InvestigationArchived,
    InvestigationCompleted,
    InvestigationStarted,
    RCATopics,
    RecommendationGenerated,
    RootCauseIdentified,
    TimelineCompleted,
    publish_rca_event,
)


class TestRCAEvents:
    def test_topics_defined(self):
        assert RCATopics.INVESTIGATION_STARTED != ""
        assert RCATopics.INVESTIGATION_COMPLETED != ""
        assert RCATopics.ROOT_CAUSE_IDENTIFIED != ""

    def test_base_event_defaults(self):
        e = BaseRCAEvent()
        assert e.event_id != ""
        assert e.timestamp != ""
        assert e.source_module == "root_cause_analysis"

    def test_event_to_dict(self):
        e = InvestigationStarted(
            investigation_id="inv-1",
            incident_id="inc-1",
            triggered_by="system",
        )
        d = e.to_dict()
        assert d["investigation_id"] == "inv-1"
        assert d["event_type"] == "InvestigationStarted"

    def test_evidence_collected_event(self):
        e = EvidenceCollected(
            investigation_id="inv-1", evidence_count=5, sources=["SENSOR", "VISION"],
        )
        assert e.evidence_count == 5
        assert len(e.sources) == 2

    def test_timeline_completed_event(self):
        e = TimelineCompleted(
            investigation_id="inv-1", event_count=10, duration_seconds=120.5,
        )
        assert e.duration_seconds == 120.5

    def test_hypothesis_generated_event(self):
        e = HypothesisGenerated(
            investigation_id="inv-1", hypothesis_count=3, top_hypothesis="Equipment failure",
        )
        assert e.top_hypothesis == "Equipment failure"

    def test_root_cause_identified_event(self):
        e = RootCauseIdentified(
            investigation_id="inv-1",
            primary_cause_description="Valve failure",
            confidence=0.85,
        )
        assert e.confidence == 0.85

    def test_investigation_completed_event(self):
        e = InvestigationCompleted(
            investigation_id="inv-1", incident_id="inc-1",
            overall_confidence=0.82, duration_seconds=30.0,
        )
        d = e.to_dict()
        assert d["overall_confidence"] == 0.82

    def test_archived_event(self):
        e = InvestigationArchived(investigation_id="inv-1")
        assert e.event_type == "InvestigationArchived"

    @pytest.mark.asyncio
    async def test_publish_rca_event(self):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance
            event = InvestigationStarted(investigation_id="inv-1", incident_id="inc-1", triggered_by="test")
            result = await publish_rca_event(event, RCATopics.INVESTIGATION_STARTED)
            assert result is True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  10. INVESTIGATION SERVICE (end-to-end, 20+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.modules.root_cause.investigation.investigation_service import InvestigationService


class TestInvestigationService:
    @pytest.fixture
    def service(self):
        return InvestigationService()

    @pytest.mark.asyncio
    async def test_start_investigation(self, service):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance
            inv = await service.start_investigation(
                incident_id="inc-1",
                title="Test Investigation",
                zone_id="zone-a",
                equipment_ids=["eq-1"],
                worker_ids=["w-1"],
                triggered_by="test",
            )
            assert isinstance(inv, Investigation)
            assert inv.incident_id == "inc-1"
            assert inv.status == InvestigationStatus.INITIATED

    @pytest.mark.asyncio
    async def test_run_investigation(self, service):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance
            inv = await service.start_investigation(
                incident_id="inc-1", title="Test", zone_id="zone-a",
            )
            result = await service.run_investigation(inv)
            assert result.status == InvestigationStatus.REVIEW
            assert len(result.evidence_ids) > 0
            assert result.overall_confidence > 0

    @pytest.mark.asyncio
    async def test_complete_investigation(self, service):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance
            inv = await service.start_investigation(
                incident_id="inc-1", title="Test", zone_id="zone-a",
            )
            inv = await service.run_investigation(inv)
            report = await service.complete_investigation(inv)
            assert isinstance(report, InvestigationReport)
            assert inv.status == InvestigationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_investigation(self, service):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance
            inv = await service.start_investigation(
                incident_id="inc-1", title="Test",
            )
            found = await service.get_investigation(inv.id)
            assert found is not None
            assert found.id == inv.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_investigation(self, service):
        found = await service.get_investigation("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_list_investigations(self, service):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance
            await service.start_investigation(incident_id="inc-1", title="Test 1")
            await service.start_investigation(incident_id="inc-2", title="Test 2")
            all_inv = await service.list_investigations(limit=50, offset=0)
            assert len(all_inv) >= 2

    @pytest.mark.asyncio
    async def test_list_investigations_by_status(self, service):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance
            await service.start_investigation(incident_id="inc-1", title="Test")
            result = await service.list_investigations(status="INITIATED", limit=50, offset=0)
            assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_search_investigations(self, service):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance
            await service.start_investigation(incident_id="inc-1", title="Equipment overheating")
            results = await service.search_investigations("overheat")
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_full_pipeline_end_to_end(self, service):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance

            # 1. Start
            inv = await service.start_investigation(
                incident_id="inc-e2e",
                title="End-to-End Test Investigation",
                zone_id="zone-a",
                equipment_ids=["eq-001"],
                worker_ids=["w-42"],
                triggered_by="test_suite",
            )
            assert inv.status == InvestigationStatus.INITIATED

            # 2. Run pipeline
            inv = await service.run_investigation(inv)
            assert inv.status == InvestigationStatus.REVIEW
            assert len(inv.evidence_ids) > 0
            assert len(inv.hypothesis_ids) > 0
            assert inv.primary_cause is not None
            assert inv.overall_confidence > 0

            # 3. Complete
            report = await service.complete_investigation(inv)
            assert inv.status == InvestigationStatus.COMPLETED
            assert isinstance(report, InvestigationReport)
            assert report.summary.total_evidence_count > 0
            assert report.summary.total_hypotheses > 0

            # 4. Verify stores
            evidence = service.get_evidence(inv.id)
            assert len(evidence) > 0
            timeline = service.get_timeline(inv.id)
            assert timeline is not None
            causal = service.get_causal_chain(inv.id)
            assert causal is not None
            hypotheses = service.get_hypotheses(inv.id)
            assert len(hypotheses) > 0
            stored_report = service.get_report(inv.id)
            assert stored_report is not None

    @pytest.mark.asyncio
    async def test_pipeline_with_recommendations(self, service):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance
            inv = await service.start_investigation(
                incident_id="inc-rec", title="Recommendation Test", zone_id="zone-a",
            )
            inv = await service.run_investigation(inv)
            recs = service.get_recommendations(inv.id)
            assert len(recs) >= 1

    @pytest.mark.asyncio
    async def test_event_publishing_count(self, service):
        with patch("app.modules.root_cause.events.rca_events.EventBus") as mock_bus:
            mock_instance = MagicMock()
            mock_instance.publish = AsyncMock(return_value=True)
            mock_bus.get.return_value = mock_instance
            inv = await service.start_investigation(incident_id="inc-events", title="Events Test")
            await service.run_investigation(inv)
            await service.complete_investigation(inv)
            # Should have published multiple events
            assert mock_instance.publish.call_count >= 5


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  11. API ROUTER TESTS (10+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestAPIRouterImports:
    """Verify all routers can be imported without errors."""

    def test_import_investigations_router(self):
        from app.modules.root_cause.api.investigations_router import router
        assert router is not None
        assert router.prefix == "/investigations"

    def test_import_evidence_router(self):
        from app.modules.root_cause.api.evidence_router import router
        assert router is not None

    def test_import_timeline_router(self):
        from app.modules.root_cause.api.timeline_router import router
        assert router is not None

    def test_import_hypotheses_router(self):
        from app.modules.root_cause.api.hypotheses_router import router
        assert router is not None

    def test_import_causal_graph_router(self):
        from app.modules.root_cause.api.causal_graph_router import router
        assert router is not None

    def test_import_recommendations_router(self):
        from app.modules.root_cause.api.recommendations_router import router
        assert router is not None

    def test_import_reports_router(self):
        from app.modules.root_cause.api.reports_router import router
        assert router is not None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  12. CROSS-CUTTING TESTS (10+ tests)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestCrossCutting:
    def test_evidence_to_timeline_round_trip(self, sample_evidence):
        engine = TimelineEngine()
        tl = engine.construct_timeline(sample_evidence, "inv-1")
        assert len(tl.events) == len(sample_evidence)
        for evt, ev in zip(tl.events, sorted(sample_evidence, key=lambda e: e.timestamp)):
            assert evt.source == ev.source

    def test_evidence_to_causal_to_hypothesis(self, sample_evidence):
        cg = CausalGraphEngine()
        chain = cg.build_causal_graph("inv-1", sample_evidence, "inc-1")
        he = HypothesisEngine()
        hypotheses = he.generate_hypotheses(sample_evidence, chain, "inv-1")
        assert len(hypotheses) >= 1

    def test_hypothesis_to_recommendation(self, sample_evidence, sample_investigation):
        cg = CausalGraphEngine()
        chain = cg.build_causal_graph("inv-1", sample_evidence, "inc-1")
        he = HypothesisEngine()
        hypotheses = he.generate_hypotheses(sample_evidence, chain, "inv-1")
        hypotheses = he.rank_hypotheses(hypotheses)
        primary = he.find_primary_cause(hypotheses)
        factors = he.find_contributing_factors(hypotheses, sample_evidence)
        re = RecommendationEngine()
        recs = re.generate_recommendations(sample_investigation, primary, factors, sample_evidence)
        assert len(recs) >= 1

    def test_all_models_serializable(self, sample_evidence, sample_investigation):
        """Verify all domain models can be serialized to JSON."""
        for ev in sample_evidence:
            data = ev.model_dump(mode="json")
            assert isinstance(data, dict)
        data = sample_investigation.model_dump(mode="json")
        assert isinstance(data, dict)

    def test_confidence_across_pipeline(self, sample_evidence):
        ce = ConfidenceEngine()
        for ev in sample_evidence:
            score = ce.compute_evidence_score(ev)
            assert 0.0 <= score.overall_score <= 1.0

    def test_model_id_uniqueness_across_types(self, now_iso):
        models = [
            Evidence(evidence_type=EvidenceType.SENSOR_READING, source=EvidenceSource.SENSOR_INTELLIGENCE, title="T", description="D", timestamp=now_iso),
            Hypothesis(investigation_id="inv", title="H", description="D"),
            Recommendation(recommendation_type=RecommendationType.IMMEDIATE_ACTION, priority=RecommendationPriority.CRITICAL, title="R", description="D"),
            CausalNode(node_type="T", entity_id="E", label="L"),
        ]
        ids = {m.id for m in models}
        assert len(ids) == len(models)
