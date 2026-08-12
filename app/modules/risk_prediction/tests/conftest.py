"""
app/modules/risk_prediction/tests/conftest.py — Shared pytest fixtures for risk prediction tests.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from app.modules.risk_prediction.domain.enums import (
    AssessmentStatus,
    EntityType,
    FeatureCategory,
    ForecastHorizon,
    MitigationPriority,
    MitigationType,
    ModelType,
    RiskLevel,
    RiskType,
    TrendDirection,
)
from app.modules.risk_prediction.domain.models import (
    CompositeRisk,
    EquipmentRisk,
    MitigationPlan,
    PlantRisk,
    RiskAssessment,
    RiskConfidence,
    RiskEvidence,
    RiskFactor,
    RiskFeature,
    RiskForecast,
    RiskPrediction,
    RiskRecommendation,
    RiskScenario,
    RiskScore,
    RiskTimeline,
    RiskTrend,
    RiskWindow,
    WorkerRisk,
    ZoneRisk,
)
from app.modules.risk_prediction.domain.events import (
    MitigationGenerated,
    PredictionCompleted,
    RiskCalculated,
    RiskEscalated,
    RiskForecastGenerated,
    RiskThresholdExceeded,
)


# ── Primitive Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def sample_sensor_ids() -> list[str]:
    return ["TEMP-001", "PRESS-002", "VIB-003", "GAS-004"]


@pytest.fixture
def sample_entity_id() -> str:
    return "EQ-PUMP-001"


@pytest.fixture
def sample_zone_id() -> str:
    return "ZONE-A-01"


@pytest.fixture
def sample_worker_id() -> str:
    return "WORKER-W-001"


@pytest.fixture
def sample_plant_id() -> str:
    return "PLANT-001"


# ── RiskScore Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def negligible_risk() -> RiskScore:
    return RiskScore.from_probability(0.05)


@pytest.fixture
def low_risk() -> RiskScore:
    return RiskScore.from_probability(0.15)


@pytest.fixture
def medium_risk() -> RiskScore:
    return RiskScore.from_probability(0.35)


@pytest.fixture
def high_risk() -> RiskScore:
    return RiskScore.from_probability(0.55)


@pytest.fixture
def critical_risk() -> RiskScore:
    return RiskScore.from_probability(0.75)


@pytest.fixture
def extreme_risk() -> RiskScore:
    return RiskScore.from_probability(0.90)


# ── RiskFeature Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def sample_sensor_features() -> list[RiskFeature]:
    return [
        RiskFeature(name="TEMP-001_rolling_mean", value=0.7, category=FeatureCategory.SENSOR, source="TEMP-001"),
        RiskFeature(name="TEMP-001_rolling_std", value=0.3, category=FeatureCategory.SENSOR, source="TEMP-001"),
        RiskFeature(name="TEMP-001_rate_of_change", value=0.5, category=FeatureCategory.SENSOR, source="TEMP-001"),
        RiskFeature(name="TEMP-001_drift_score", value=0.4, category=FeatureCategory.SENSOR, source="TEMP-001"),
        RiskFeature(name="sensor_aggregate_anomaly_count", value=3.0, category=FeatureCategory.SENSOR, source="aggregate"),
        RiskFeature(name="sensor_critical_count", value=1.0, category=FeatureCategory.SENSOR, source="aggregate"),
        RiskFeature(name="sensor_health_score", value=0.8, category=FeatureCategory.SENSOR, source="aggregate"),
    ]


@pytest.fixture
def sample_vision_features() -> list[RiskFeature]:
    return [
        RiskFeature(name="vision_ppe_compliance_score", value=0.75, category=FeatureCategory.VISION, source="vision"),
        RiskFeature(name="vision_worker_count", value=3.0, category=FeatureCategory.VISION, source="vision"),
        RiskFeature(name="vision_violation_count", value=1.0, category=FeatureCategory.VISION, source="vision"),
        RiskFeature(name="vision_anomaly_score", value=0.2, category=FeatureCategory.VISION, source="vision"),
        RiskFeature(name="vision_fire_detection_score", value=0.05, category=FeatureCategory.VISION, source="vision"),
        RiskFeature(name="vision_fall_detection_score", value=0.0, category=FeatureCategory.VISION, source="vision"),
    ]


@pytest.fixture
def sample_graph_features() -> list[RiskFeature]:
    return [
        RiskFeature(name="graph_degree_centrality", value=0.3, category=FeatureCategory.GRAPH, source="graph"),
        RiskFeature(name="graph_hazard_proximity", value=0.4, category=FeatureCategory.GRAPH, source="graph"),
        RiskFeature(name="graph_dependency_score", value=0.5, category=FeatureCategory.GRAPH, source="graph"),
        RiskFeature(name="graph_critical_path_score", value=0.0, category=FeatureCategory.GRAPH, source="graph"),
        RiskFeature(name="graph_impact_radius", value=0.2, category=FeatureCategory.GRAPH, source="graph"),
        RiskFeature(name="graph_historical_failure_count", value=1.0, category=FeatureCategory.GRAPH, source="graph"),
    ]


@pytest.fixture
def sample_graphrag_features() -> list[RiskFeature]:
    return [
        RiskFeature(name="graphrag_historical_similarity", value=0.4, category=FeatureCategory.GRAPHRAG, source="graphrag"),
        RiskFeature(name="graphrag_incident_frequency", value=0.2, category=FeatureCategory.GRAPHRAG, source="graphrag"),
        RiskFeature(name="graphrag_root_cause_recurrence", value=0.15, category=FeatureCategory.GRAPHRAG, source="graphrag"),
        RiskFeature(name="graphrag_similar_failure_count", value=0.1, category=FeatureCategory.GRAPHRAG, source="graphrag"),
    ]


@pytest.fixture
def sample_all_features(
    sample_sensor_features,
    sample_vision_features,
    sample_graph_features,
    sample_graphrag_features,
) -> list[RiskFeature]:
    return sample_sensor_features + sample_vision_features + sample_graph_features + sample_graphrag_features


@pytest.fixture
def sample_feature_array(sample_all_features) -> tuple[np.ndarray, list[str]]:
    names = [f.name for f in sample_all_features]
    values = np.array([f.value for f in sample_all_features])
    return values, names


# ── RiskFactor Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def sample_risk_factors() -> list[RiskFactor]:
    return [
        RiskFactor(
            name="High temperature rolling mean",
            weight=0.35,
            contribution=0.28,
            category=FeatureCategory.SENSOR,
            description="Temperature sensor shows elevated rolling mean above baseline",
        ),
        RiskFactor(
            name="PPE compliance below threshold",
            weight=0.25,
            contribution=0.18,
            category=FeatureCategory.VISION,
            description="Vision system detected PPE compliance at 75%, below 85% threshold",
        ),
        RiskFactor(
            name="High hazard proximity",
            weight=0.20,
            contribution=0.12,
            category=FeatureCategory.GRAPH,
            description="Equipment is adjacent to 2 hazardous nodes in Knowledge Graph",
        ),
        RiskFactor(
            name="Historical failure similarity",
            weight=0.20,
            contribution=0.08,
            category=FeatureCategory.GRAPHRAG,
            description="40% similarity to previous pump failures in maintenance history",
        ),
    ]


# ── RiskEvidence Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def sample_evidence() -> list[RiskEvidence]:
    return [
        RiskEvidence(
            source="SENSOR_INTELLIGENCE",
            content="Temperature sensor TEMP-001 shows 15% above baseline with 0.7 z-score",
            confidence=0.85,
            citations=["sensor:TEMP-001:reading-xyz"],
            evidence_type="SENSOR",
        ),
        RiskEvidence(
            source="VISION_INTELLIGENCE",
            content="Worker without hard hat detected in zone at 14:22 UTC",
            confidence=0.92,
            citations=["camera:CAM-003:frame-445"],
            evidence_type="VISION",
        ),
        RiskEvidence(
            source="KNOWLEDGE_GRAPH",
            content="Equipment EQ-PUMP-001 has 3 direct connections to high-risk nodes",
            confidence=0.95,
            citations=["node:EQ-PUMP-001", "rel:HAS_RISK"],
            evidence_type="GRAPH",
        ),
        RiskEvidence(
            source="GRAPHRAG",
            content="Found 2 similar pump failures in maintenance history from 2024-2025",
            confidence=0.78,
            citations=["doc:maint-report-2024-11", "doc:incident-2025-03"],
            evidence_type="GRAPHRAG",
        ),
    ]


# ── RiskConfidence Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def high_confidence() -> RiskConfidence:
    return RiskConfidence(
        overall=0.88,
        sensor_completeness=0.95,
        vision_completeness=0.90,
        graph_completeness=0.85,
        graphrag_completeness=0.80,
        feature_count=23,
        missing_feature_count=2,
    )


@pytest.fixture
def partial_confidence() -> RiskConfidence:
    return RiskConfidence(
        overall=0.60,
        sensor_completeness=0.50,
        vision_completeness=0.0,
        graph_completeness=0.80,
        graphrag_completeness=0.70,
        feature_count=15,
        missing_feature_count=8,
    )


# ── RiskWindow Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def window_5min() -> RiskWindow:
    return RiskWindow.for_horizon(ForecastHorizon.FIVE_MIN)


@pytest.fixture
def window_1hour() -> RiskWindow:
    return RiskWindow.for_horizon(ForecastHorizon.ONE_HOUR)


@pytest.fixture
def window_24hour() -> RiskWindow:
    return RiskWindow.for_horizon(ForecastHorizon.TWENTY_FOUR_HOUR)


# ── RiskPrediction Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def sample_prediction(medium_risk, sample_risk_factors, sample_evidence, high_confidence, window_5min) -> RiskPrediction:
    return RiskPrediction(
        risk_type=RiskType.EQUIPMENT_FAILURE,
        risk_score=medium_risk,
        factors=sample_risk_factors,
        evidence=sample_evidence,
        confidence=high_confidence,
        window=window_5min,
        model_type=ModelType.ENSEMBLE,
        features_used=["TEMP-001_rolling_mean", "vision_ppe_compliance_score"],
        explanation="Medium equipment failure risk driven primarily by elevated temperature readings and reduced PPE compliance.",
    )


# ── RiskForecast Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def sample_forecast(sample_entity_id, medium_risk, sample_risk_factors, sample_evidence, high_confidence) -> RiskForecast:
    predictions = {}
    for horizon in ForecastHorizon:
        window = RiskWindow.for_horizon(horizon)
        # Increase probability with horizon to simulate trend
        prob = 0.35 + (horizon.minutes / 10080) * 0.15
        predictions[horizon.value] = RiskPrediction(
            risk_type=RiskType.EQUIPMENT_FAILURE,
            risk_score=RiskScore.from_probability(min(prob, 0.95), confidence=0.85),
            factors=sample_risk_factors[:2],
            evidence=sample_evidence[:2],
            confidence=high_confidence,
            window=window,
            model_type=ModelType.ENSEMBLE,
        )
    return RiskForecast(
        entity_id=sample_entity_id,
        entity_type=EntityType.EQUIPMENT,
        predictions=predictions,
        trend=RiskTrend(
            direction=TrendDirection.INCREASING,
            slope=0.001,
            magnitude=0.15,
            window_minutes=60,
        ),
        dominant_risk_type=RiskType.EQUIPMENT_FAILURE,
    )


# ── RiskRecommendation Fixtures ────────────────────────────────────────────────

@pytest.fixture
def sample_recommendations() -> list[RiskRecommendation]:
    return [
        RiskRecommendation(
            mitigation_type=MitigationType.INSPECTION,
            priority=MitigationPriority.URGENT,
            title="Inspect TEMP-001 sensor and pump bearings",
            description="Conduct immediate visual and thermal inspection of pump bearings. Check sensor calibration.",
            rationale="Elevated temperature trend suggests bearing wear or sensor drift",
            estimated_risk_reduction=0.20,
            time_to_implement="2 hours",
            resources_required=["Maintenance technician", "Thermal camera"],
        ),
        RiskRecommendation(
            mitigation_type=MitigationType.PPE_RECOMMENDATION,
            priority=MitigationPriority.HIGH,
            title="Enforce PPE compliance in zone",
            description="All workers in zone must wear hard hats and safety glasses immediately.",
            rationale="Vision system detected PPE violations",
            estimated_risk_reduction=0.15,
            time_to_implement="15 minutes",
            resources_required=["Zone supervisor", "PPE equipment"],
        ),
        RiskRecommendation(
            mitigation_type=MitigationType.MONITORING_INCREASE,
            priority=MitigationPriority.MEDIUM,
            title="Increase monitoring frequency to every 5 minutes",
            description="Set sensor polling to 5-minute intervals for next 4 hours.",
            rationale="Elevated risk warrants higher monitoring frequency",
            estimated_risk_reduction=0.05,
            time_to_implement="5 minutes",
            resources_required=["Operator"],
        ),
    ]


# ── MitigationPlan Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def sample_mitigation_plan(sample_entity_id, sample_recommendations) -> MitigationPlan:
    return MitigationPlan(
        entity_id=sample_entity_id,
        entity_type=EntityType.EQUIPMENT,
        recommendations=sample_recommendations,
        total_estimated_risk_reduction=0.36,
        approval_required=True,
        timeline="2 hours for complete implementation",
        knowledge_graph_path=["EQ-PUMP-001", "ZONE-A-01", "PLANT-001"],
        evidence_sources=["SENSOR_INTELLIGENCE", "VISION_INTELLIGENCE", "KNOWLEDGE_GRAPH"],
    )


# ── RiskTrend Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def increasing_trend() -> RiskTrend:
    return RiskTrend(direction=TrendDirection.INCREASING, slope=0.005, magnitude=0.2, window_minutes=60)


@pytest.fixture
def stable_trend() -> RiskTrend:
    return RiskTrend(direction=TrendDirection.STABLE, slope=0.0, magnitude=0.02, window_minutes=60)


@pytest.fixture
def decreasing_trend() -> RiskTrend:
    return RiskTrend(direction=TrendDirection.DECREASING, slope=-0.003, magnitude=0.1, window_minutes=60)


# ── RiskAssessment Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def sample_assessment(
    sample_entity_id,
    medium_risk,
    sample_risk_factors,
    sample_evidence,
    sample_forecast,
    sample_mitigation_plan,
    increasing_trend,
) -> RiskAssessment:
    return RiskAssessment(
        entity_id=sample_entity_id,
        entity_type=EntityType.EQUIPMENT,
        status=AssessmentStatus.COMPLETED,
        current_risk=medium_risk,
        forecast=sample_forecast,
        mitigation_plan=sample_mitigation_plan,
        trend=increasing_trend,
        top_factors=sample_risk_factors,
        evidence=sample_evidence,
        explanation="Medium equipment failure risk detected. Primary driver: elevated temperature readings with increasing trend. Secondary: PPE compliance below threshold.",
        graphrag_citations=["doc:maint-report-2024-11"],
        root_cause_refs=["rca:investigation-2024-pump-failure"],
        latency_ms=145.3,
        feature_vector_size=23,
        risk_types_detected=[RiskType.EQUIPMENT_FAILURE, RiskType.OPERATIONAL],
    )


@pytest.fixture
def high_risk_assessment(
    sample_entity_id,
    high_risk,
    sample_risk_factors,
    sample_evidence,
) -> RiskAssessment:
    return RiskAssessment(
        entity_id=sample_entity_id,
        entity_type=EntityType.EQUIPMENT,
        status=AssessmentStatus.COMPLETED,
        current_risk=high_risk,
        top_factors=sample_risk_factors,
        evidence=sample_evidence,
        explanation="High equipment failure risk. Immediate intervention required.",
        latency_ms=120.0,
        feature_vector_size=23,
        risk_types_detected=[RiskType.EQUIPMENT_FAILURE],
    )


# ── Specialized Risk Assessment Fixtures ──────────────────────────────────────

@pytest.fixture
def sample_equipment_risk(sample_assessment) -> EquipmentRisk:
    return EquipmentRisk(
        assessment=sample_assessment,
        equipment_id="EQ-PUMP-001",
        equipment_type="CENTRIFUGAL_PUMP",
        equipment_name="Main Process Pump A",
        maintenance_overdue=False,
        days_since_maintenance=15.0,
        last_maintenance_date="2026-07-17T00:00:00+00:00",
        failure_probability=0.35,
        estimated_rul=120.0,
        anomalous_sensor_ids=["TEMP-001"],
        connected_equipment_ids=["EQ-MOTOR-001", "EQ-VALVE-002"],
    )


@pytest.fixture
def sample_worker_risk(sample_assessment, sample_zone_id) -> WorkerRisk:
    return WorkerRisk(
        assessment=sample_assessment,
        worker_id="WORKER-W-001",
        worker_role="Process Operator",
        zone_id=sample_zone_id,
        exposure_duration_hours=4.5,
        ppe_compliance_score=0.75,
        proximity_to_hazards=["HAZARD-GAS-001"],
        violation_count_24h=1,
    )


@pytest.fixture
def sample_zone_risk(sample_assessment, sample_zone_id) -> ZoneRisk:
    return ZoneRisk(
        assessment=sample_assessment,
        zone_id=sample_zone_id,
        zone_name="Process Area A",
        worker_count=5,
        equipment_ids=["EQ-PUMP-001", "EQ-MOTOR-001"],
        hazard_types=[RiskType.EQUIPMENT_FAILURE, RiskType.GAS_LEAK],
        max_equipment_risk=0.55,
        avg_worker_ppe_compliance=0.75,
    )


@pytest.fixture
def sample_plant_risk(sample_assessment, sample_plant_id) -> PlantRisk:
    return PlantRisk(
        assessment=sample_assessment,
        plant_id=sample_plant_id,
        plant_name="Refinery Plant 1",
        zone_count=8,
        active_hazard_count=3,
        overall_safety_index=0.72,
        critical_zone_ids=[],
        critical_equipment_ids=["EQ-PUMP-001"],
        environmental_risk=0.12,
        operational_risk=0.35,
    )


@pytest.fixture
def sample_composite_risk(sample_entity_id, medium_risk) -> CompositeRisk:
    return CompositeRisk(
        entity_id=sample_entity_id,
        entity_type=EntityType.EQUIPMENT,
        equipment_risk=medium_risk,
        worker_risk=RiskScore.from_probability(0.25),
        zone_risk=RiskScore.from_probability(0.30),
        environmental_risk=RiskScore.from_probability(0.10),
        operational_risk=RiskScore.from_probability(0.28),
        composite_score=medium_risk,
        weights_used={"equipment": 0.30, "worker": 0.25, "zone": 0.20, "environmental": 0.15, "operational": 0.10},
    )


@pytest.fixture
def sample_scenario(sample_entity_id, medium_risk, high_risk) -> RiskScenario:
    return RiskScenario(
        name="High temperature scenario",
        description="What if temperature sensor shows 20% above baseline?",
        entity_id=sample_entity_id,
        entity_type=EntityType.EQUIPMENT,
        modified_conditions={"TEMP-001_rolling_mean": 0.9, "TEMP-001_rate_of_change": 0.8},
        baseline_risk=medium_risk,
        scenario_risk=high_risk,
        delta=0.20,
        feasibility=0.85,
        mitigation_scenario=False,
    )


# ── Domain Event Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def risk_calculated_event(sample_entity_id, sample_assessment) -> RiskCalculated:
    return RiskCalculated(
        entity_id=sample_entity_id,
        entity_type=EntityType.EQUIPMENT,
        assessment_id=sample_assessment.assessment_id,
        risk_value=sample_assessment.current_risk.value,
        risk_level=sample_assessment.current_risk.level,
        confidence=0.88,
        dominant_risk_type=RiskType.EQUIPMENT_FAILURE,
        latency_ms=145.3,
    )


@pytest.fixture
def risk_forecast_event(sample_forecast) -> RiskForecastGenerated:
    return RiskForecastGenerated(
        forecast_id=sample_forecast.forecast_id,
        entity_id=sample_forecast.entity_id,
        entity_type=sample_forecast.entity_type,
        horizons=[h.value for h in ForecastHorizon],
        peak_risk_value=0.50,
        peak_horizon=ForecastHorizon.SEVEN_DAY.value,
    )


@pytest.fixture
def threshold_exceeded_event(sample_entity_id) -> RiskThresholdExceeded:
    return RiskThresholdExceeded(
        entity_id=sample_entity_id,
        entity_type=EntityType.EQUIPMENT,
        risk_type=RiskType.EQUIPMENT_FAILURE,
        threshold_value=0.50,
        actual_value=0.55,
        risk_level=RiskLevel.HIGH,
        previous_level=RiskLevel.MEDIUM,
    )


@pytest.fixture
def mitigation_generated_event(sample_mitigation_plan, sample_assessment) -> MitigationGenerated:
    return MitigationGenerated(
        plan_id=sample_mitigation_plan.plan_id,
        entity_id=sample_mitigation_plan.entity_id,
        entity_type=sample_mitigation_plan.entity_type,
        recommendation_count=len(sample_mitigation_plan.recommendations),
        estimated_risk_reduction=sample_mitigation_plan.total_estimated_risk_reduction,
        has_immediate_actions=len(sample_mitigation_plan.immediate_actions) > 0,
        has_evacuation=sample_mitigation_plan.has_evacuation,
        assessment_id=sample_assessment.assessment_id,
    )


@pytest.fixture
def risk_escalated_event(sample_entity_id) -> RiskEscalated:
    return RiskEscalated(
        entity_id=sample_entity_id,
        entity_type=EntityType.EQUIPMENT,
        from_level=RiskLevel.MEDIUM,
        to_level=RiskLevel.HIGH,
        risk_type=RiskType.EQUIPMENT_FAILURE,
        risk_value=0.55,
        escalation_velocity=0.005,
    )


@pytest.fixture
def prediction_completed_event(sample_prediction) -> PredictionCompleted:
    return PredictionCompleted(
        prediction_id=sample_prediction.prediction_id,
        entity_id="EQ-PUMP-001",
        entity_type=EntityType.EQUIPMENT,
        latency_ms=145.3,
        confidence=0.88,
        feature_count=23,
        model_type=ModelType.ENSEMBLE.value,
        horizons_generated=7,
    )


# ── Mock Service Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def mock_risk_repository():
    repo = AsyncMock()
    repo.save_assessment = AsyncMock()
    repo.get_assessment = AsyncMock(return_value=None)
    repo.get_latest_assessment = AsyncMock(return_value=None)
    repo.list_assessments = AsyncMock(return_value=([], 0))
    repo.save_forecast = AsyncMock()
    repo.get_forecast = AsyncMock(return_value=None)
    repo.save_mitigation_plan = AsyncMock()
    repo.get_mitigation_plan = AsyncMock(return_value=None)
    repo.save_scenario = AsyncMock()
    repo.list_scenarios = AsyncMock(return_value=[])
    repo.get_risk_history = AsyncMock(return_value=RiskTimeline(entity_id="test", entity_type=EntityType.EQUIPMENT))
    repo.get_analytics_summary = AsyncMock(return_value={})
    return repo


@pytest.fixture
def mock_event_publisher():
    publisher = AsyncMock()
    publisher.publish_risk_calculated = AsyncMock()
    publisher.publish_forecast_generated = AsyncMock()
    publisher.publish_threshold_exceeded = AsyncMock()
    publisher.publish_mitigation_generated = AsyncMock()
    publisher.publish_risk_escalated = AsyncMock()
    publisher.publish_prediction_completed = AsyncMock()
    return publisher


@pytest.fixture
def mock_graph_service():
    service = AsyncMock()
    from app.modules.risk_prediction.application.graph.graph_risk_service import GraphContext
    service.get_entity_graph_context = AsyncMock(
        return_value=GraphContext(
            entity_id="EQ-PUMP-001",
            entity_type=EntityType.EQUIPMENT,
            neighbor_count=4,
            hazard_node_ids=["HAZARD-001"],
            dependency_ids=["EQ-MOTOR-001"],
            centrality_score=0.3,
            is_on_critical_path=False,
            impact_radius=3,
            failure_history=[],
            maintenance_history=[{"date": "2026-07-17", "type": "preventive"}],
        )
    )
    service.sync_risk_node = AsyncMock()
    service.sync_forecast_node = AsyncMock()
    service.sync_mitigation_node = AsyncMock()
    service.compute_impact_radius = AsyncMock(return_value=["EQ-MOTOR-001", "ZONE-A-01"])
    service.get_hazard_nodes = AsyncMock(return_value=[])
    service.get_risk_propagation_path = AsyncMock(return_value=[])
    return service
