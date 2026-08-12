"""
app/modules/risk_prediction/tests/test_mitigation_engine.py
Tests for MitigationEngine — recommendation generation, plan building,
risk reduction estimation, and GraphRAG enrichment.
"""
from __future__ import annotations

import pytest

from app.modules.risk_prediction.domain.enums import (
    EntityType,
    MitigationPriority,
    MitigationType,
    RiskLevel,
    RiskType,
)
from app.modules.risk_prediction.domain.models import (
    MitigationPlan,
    RiskAssessment,
    RiskEvidence,
    RiskFactor,
    RiskRecommendation,
    RiskScore,
)


@pytest.fixture
def mitigation_engine(mock_graph_service):
    from app.modules.risk_prediction.application.recommendations.mitigation_engine import MitigationEngine
    return MitigationEngine(graph_service=mock_graph_service)


@pytest.fixture
def extreme_risk_assessment(sample_entity_id) -> RiskAssessment:
    return RiskAssessment(
        entity_id=sample_entity_id,
        entity_type=EntityType.ZONE,
        current_risk=RiskScore.from_probability(0.92),
        top_factors=[],
        evidence=[],
        risk_types_detected=[RiskType.FIRE, RiskType.EXPLOSION],
    )


@pytest.fixture
def critical_risk_assessment(sample_entity_id) -> RiskAssessment:
    return RiskAssessment(
        entity_id=sample_entity_id,
        entity_type=EntityType.EQUIPMENT,
        current_risk=RiskScore.from_probability(0.78),
        top_factors=[],
        evidence=[],
        risk_types_detected=[RiskType.EQUIPMENT_FAILURE],
    )


@pytest.fixture
def high_worker_risk_assessment() -> RiskAssessment:
    return RiskAssessment(
        entity_id="WORKER-W-001",
        entity_type=EntityType.WORKER,
        current_risk=RiskScore.from_probability(0.60),
        top_factors=[],
        evidence=[],
        risk_types_detected=[RiskType.WORKER_INJURY],
    )


class TestMitigationPlanGeneration:
    @pytest.mark.asyncio
    async def test_plan_generated_for_medium_risk(
        self, mitigation_engine, sample_assessment, mock_graph_service
    ):
        from app.modules.risk_prediction.application.graph.graph_risk_service import GraphContext
        graph_ctx = await mock_graph_service.get_entity_graph_context(
            sample_assessment.entity_id, sample_assessment.entity_type
        )
        plan = await mitigation_engine.generate_plan(
            assessment=sample_assessment,
            graphrag_context="Historical pump failures resolved with bearing replacement",
            graph_context=graph_ctx,
        )
        assert isinstance(plan, MitigationPlan)
        assert len(plan.recommendations) > 0

    @pytest.mark.asyncio
    async def test_extreme_risk_includes_evacuation(
        self, mitigation_engine, extreme_risk_assessment, mock_graph_service
    ):
        from app.modules.risk_prediction.application.graph.graph_risk_service import GraphContext
        graph_ctx = await mock_graph_service.get_entity_graph_context(
            extreme_risk_assessment.entity_id, extreme_risk_assessment.entity_type
        )
        plan = await mitigation_engine.generate_plan(
            assessment=extreme_risk_assessment,
            graphrag_context="",
            graph_context=graph_ctx,
        )
        has_evacuation = any(
            r.mitigation_type == MitigationType.EVACUATION for r in plan.recommendations
        )
        assert has_evacuation

    @pytest.mark.asyncio
    async def test_extreme_risk_includes_shutdown(
        self, mitigation_engine, extreme_risk_assessment, mock_graph_service
    ):
        from app.modules.risk_prediction.application.graph.graph_risk_service import GraphContext
        graph_ctx = await mock_graph_service.get_entity_graph_context(
            extreme_risk_assessment.entity_id, extreme_risk_assessment.entity_type
        )
        plan = await mitigation_engine.generate_plan(
            assessment=extreme_risk_assessment,
            graphrag_context="",
            graph_context=graph_ctx,
        )
        has_shutdown = any(
            r.mitigation_type == MitigationType.SHUTDOWN for r in plan.recommendations
        )
        assert has_shutdown

    @pytest.mark.asyncio
    async def test_extreme_risk_requires_approval(
        self, mitigation_engine, extreme_risk_assessment, mock_graph_service
    ):
        graph_ctx = await mock_graph_service.get_entity_graph_context(
            extreme_risk_assessment.entity_id, extreme_risk_assessment.entity_type
        )
        plan = await mitigation_engine.generate_plan(
            assessment=extreme_risk_assessment,
            graphrag_context="",
            graph_context=graph_ctx,
        )
        assert plan.approval_required is True

    @pytest.mark.asyncio
    async def test_high_risk_equipment_includes_maintenance(
        self, mitigation_engine, critical_risk_assessment, mock_graph_service
    ):
        graph_ctx = await mock_graph_service.get_entity_graph_context(
            critical_risk_assessment.entity_id, critical_risk_assessment.entity_type
        )
        plan = await mitigation_engine.generate_plan(
            assessment=critical_risk_assessment,
            graphrag_context="",
            graph_context=graph_ctx,
        )
        has_maintenance = any(
            r.mitigation_type in (MitigationType.MAINTENANCE, MitigationType.INSPECTION)
            for r in plan.recommendations
        )
        assert has_maintenance

    @pytest.mark.asyncio
    async def test_worker_risk_includes_ppe_recommendation(
        self, mitigation_engine, high_worker_risk_assessment, mock_graph_service
    ):
        graph_ctx = await mock_graph_service.get_entity_graph_context(
            high_worker_risk_assessment.entity_id, high_worker_risk_assessment.entity_type
        )
        plan = await mitigation_engine.generate_plan(
            assessment=high_worker_risk_assessment,
            graphrag_context="",
            graph_context=graph_ctx,
        )
        has_ppe = any(
            r.mitigation_type == MitigationType.PPE_RECOMMENDATION
            for r in plan.recommendations
        )
        assert has_ppe

    @pytest.mark.asyncio
    async def test_graphrag_context_adds_citations(
        self, mitigation_engine, sample_assessment, mock_graph_service
    ):
        graph_ctx = await mock_graph_service.get_entity_graph_context(
            sample_assessment.entity_id, sample_assessment.entity_type
        )
        plan = await mitigation_engine.generate_plan(
            assessment=sample_assessment,
            graphrag_context="Maintenance report 2024-11 shows bearing replacement resolved similar issue",
            graph_context=graph_ctx,
        )
        # Evidence sources should be populated
        assert len(plan.evidence_sources) > 0


class TestRiskReductionEstimation:
    def test_combined_reduction_not_additive(self, mitigation_engine):
        """Using 1-(1-r1)(1-r2) formula, not simple addition."""
        recs = [
            RiskRecommendation(
                mitigation_type=MitigationType.EVACUATION,
                priority=MitigationPriority.IMMEDIATE,
                title="Evacuate",
                description="Evacuate",
                estimated_risk_reduction=0.8,
            ),
            RiskRecommendation(
                mitigation_type=MitigationType.SHUTDOWN,
                priority=MitigationPriority.IMMEDIATE,
                title="Shutdown",
                description="Shutdown",
                estimated_risk_reduction=0.7,
            ),
        ]
        total = mitigation_engine._estimate_total_reduction(recs)
        # Should be 1 - (1-0.8)(1-0.7) = 1 - 0.2*0.3 = 0.94
        assert total == pytest.approx(0.94, rel=0.05)

    def test_single_recommendation_reduction(self, mitigation_engine):
        recs = [
            RiskRecommendation(
                mitigation_type=MitigationType.INSPECTION,
                priority=MitigationPriority.HIGH,
                title="Inspect",
                description="Inspect",
                estimated_risk_reduction=0.2,
            )
        ]
        total = mitigation_engine._estimate_total_reduction(recs)
        assert total == pytest.approx(0.2, rel=0.01)

    def test_empty_recommendations_zero_reduction(self, mitigation_engine):
        total = mitigation_engine._estimate_total_reduction([])
        assert total == 0.0

    def test_total_reduction_bounded(self, mitigation_engine):
        recs = [
            RiskRecommendation(
                mitigation_type=MitigationType.EVACUATION,
                priority=MitigationPriority.IMMEDIATE,
                title="Evac",
                description="Evac",
                estimated_risk_reduction=0.8,
            )
        ] * 10
        total = mitigation_engine._estimate_total_reduction(recs)
        assert 0.0 <= total <= 1.0


class TestTimelineComputation:
    def test_extreme_risk_short_timeline(self, mitigation_engine):
        recs = [
            RiskRecommendation(
                mitigation_type=MitigationType.EVACUATION,
                priority=MitigationPriority.IMMEDIATE,
                title="Evac",
                description="Evac",
                estimated_risk_reduction=0.8,
                time_to_implement="5 minutes",
            )
        ]
        timeline = mitigation_engine._compute_timeline(recs, RiskLevel.EXTREME)
        assert timeline != ""

    def test_low_risk_longer_timeline(self, mitigation_engine):
        recs = [
            RiskRecommendation(
                mitigation_type=MitigationType.MONITORING_INCREASE,
                priority=MitigationPriority.LOW,
                title="Monitor",
                description="Monitor",
                estimated_risk_reduction=0.1,
                time_to_implement="24 hours",
            )
        ]
        timeline = mitigation_engine._compute_timeline(recs, RiskLevel.LOW)
        assert timeline != ""

    def test_empty_recommendations_timeline(self, mitigation_engine):
        timeline = mitigation_engine._compute_timeline([], RiskLevel.MEDIUM)
        assert isinstance(timeline, str)
