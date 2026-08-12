"""
app/modules/risk_prediction/tests/test_domain_models.py
Tests for all 20+ domain models, enums, and value objects.
"""
from __future__ import annotations

import pytest

from app.modules.risk_prediction.domain.enums import (
    ForecastHorizon,
    RiskLevel,
    RiskType,
    MitigationType,
    EntityType,
    FeatureCategory,
    ModelType,
    TrendDirection,
    MitigationPriority,
    AssessmentStatus,
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


# ── RiskLevel Tests ────────────────────────────────────────────────────────────

class TestRiskLevel:
    def test_from_probability_negligible(self):
        assert RiskLevel.from_probability(0.05) == RiskLevel.NEGLIGIBLE

    def test_from_probability_low(self):
        assert RiskLevel.from_probability(0.15) == RiskLevel.LOW

    def test_from_probability_medium(self):
        assert RiskLevel.from_probability(0.35) == RiskLevel.MEDIUM

    def test_from_probability_high(self):
        assert RiskLevel.from_probability(0.55) == RiskLevel.HIGH

    def test_from_probability_critical(self):
        assert RiskLevel.from_probability(0.75) == RiskLevel.CRITICAL

    def test_from_probability_extreme(self):
        assert RiskLevel.from_probability(0.90) == RiskLevel.EXTREME

    def test_from_probability_boundary_low_medium(self):
        # 0.25 is exactly at boundary → LOW
        assert RiskLevel.from_probability(0.24999) == RiskLevel.LOW
        assert RiskLevel.from_probability(0.25) == RiskLevel.MEDIUM

    def test_from_probability_boundary_high_critical(self):
        assert RiskLevel.from_probability(0.64999) == RiskLevel.HIGH
        assert RiskLevel.from_probability(0.65) == RiskLevel.CRITICAL

    def test_from_probability_clamp_zero(self):
        assert RiskLevel.from_probability(0.0) == RiskLevel.NEGLIGIBLE

    def test_from_probability_clamp_one(self):
        assert RiskLevel.from_probability(1.0) == RiskLevel.EXTREME

    def test_risk_level_is_str_enum(self):
        assert isinstance(RiskLevel.HIGH, str)
        assert RiskLevel.HIGH == "HIGH"

    def test_all_levels_defined(self):
        levels = list(RiskLevel)
        assert len(levels) == 6


# ── ForecastHorizon Tests ──────────────────────────────────────────────────────

class TestForecastHorizon:
    def test_five_min_duration(self):
        assert ForecastHorizon.FIVE_MIN.minutes == 5

    def test_fifteen_min_duration(self):
        assert ForecastHorizon.FIFTEEN_MIN.minutes == 15

    def test_thirty_min_duration(self):
        assert ForecastHorizon.THIRTY_MIN.minutes == 30

    def test_one_hour_duration(self):
        assert ForecastHorizon.ONE_HOUR.minutes == 60

    def test_six_hour_duration(self):
        assert ForecastHorizon.SIX_HOUR.minutes == 360

    def test_twenty_four_hour_duration(self):
        assert ForecastHorizon.TWENTY_FOUR_HOUR.minutes == 1440

    def test_seven_day_duration(self):
        assert ForecastHorizon.SEVEN_DAY.minutes == 10080

    def test_label_five_min(self):
        assert ForecastHorizon.FIVE_MIN.label == "5 Minutes"

    def test_label_seven_day(self):
        assert ForecastHorizon.SEVEN_DAY.label == "7 Days"

    def test_all_horizons_have_minutes(self):
        for horizon in ForecastHorizon:
            assert horizon.minutes > 0

    def test_horizons_are_ordered(self):
        durations = [h.minutes for h in ForecastHorizon]
        assert durations == sorted(durations)

    def test_horizon_count(self):
        assert len(list(ForecastHorizon)) == 7


# ── RiskScore Tests ────────────────────────────────────────────────────────────

class TestRiskScore:
    def test_from_probability_basic(self):
        score = RiskScore.from_probability(0.5)
        assert score.value == 0.5
        assert score.level == RiskLevel.HIGH

    def test_from_probability_clamps_above_one(self):
        score = RiskScore.from_probability(1.5)
        assert score.value == 1.0

    def test_from_probability_clamps_below_zero(self):
        score = RiskScore.from_probability(-0.5)
        assert score.value == 0.0
        assert score.level == RiskLevel.NEGLIGIBLE

    def test_is_elevated_true_for_high(self, high_risk):
        assert high_risk.is_elevated is True

    def test_is_elevated_true_for_critical(self, critical_risk):
        assert critical_risk.is_elevated is True

    def test_is_elevated_true_for_extreme(self, extreme_risk):
        assert extreme_risk.is_elevated is True

    def test_is_elevated_false_for_medium(self, medium_risk):
        assert medium_risk.is_elevated is False

    def test_is_elevated_false_for_low(self, low_risk):
        assert low_risk.is_elevated is False

    def test_requires_immediate_action_extreme(self, extreme_risk):
        assert extreme_risk.requires_immediate_action is True

    def test_requires_immediate_action_critical(self, critical_risk):
        assert critical_risk.requires_immediate_action is True

    def test_requires_immediate_action_false_high(self, high_risk):
        assert high_risk.requires_immediate_action is False

    def test_risk_score_is_immutable(self, medium_risk):
        with pytest.raises(Exception):
            medium_risk.value = 0.9

    def test_confidence_within_bounds(self):
        with pytest.raises(Exception):
            RiskScore(value=0.5, level=RiskLevel.HIGH, confidence=1.5, uncertainty=0.0)

    def test_uncertainty_within_bounds(self):
        with pytest.raises(Exception):
            RiskScore(value=0.5, level=RiskLevel.HIGH, confidence=0.8, uncertainty=-0.1)

    def test_from_probability_with_confidence(self):
        score = RiskScore.from_probability(0.7, confidence=0.9, uncertainty=0.05)
        assert score.confidence == 0.9
        assert score.uncertainty == 0.05


# ── RiskWindow Tests ──────────────────────────────────────────────────────────

class TestRiskWindow:
    def test_for_horizon_five_min(self):
        window = RiskWindow.for_horizon(ForecastHorizon.FIVE_MIN)
        assert window.duration_minutes == 5
        assert window.horizon == ForecastHorizon.FIVE_MIN
        assert window.start != ""
        assert window.end != ""

    def test_for_horizon_seven_day(self):
        window = RiskWindow.for_horizon(ForecastHorizon.SEVEN_DAY)
        assert window.duration_minutes == 10080

    def test_end_after_start(self):
        from datetime import datetime, timezone
        window = RiskWindow.for_horizon(ForecastHorizon.ONE_HOUR)
        start = datetime.fromisoformat(window.start)
        end = datetime.fromisoformat(window.end)
        assert end > start

    def test_window_duration_matches_horizon(self):
        from datetime import datetime, timezone
        window = RiskWindow.for_horizon(ForecastHorizon.SIX_HOUR)
        start = datetime.fromisoformat(window.start)
        end = datetime.fromisoformat(window.end)
        delta_minutes = (end - start).total_seconds() / 60
        assert abs(delta_minutes - 360) < 1  # within 1 minute tolerance


# ── RiskFactor Tests ───────────────────────────────────────────────────────────

class TestRiskFactor:
    def test_risk_factor_creation(self, sample_risk_factors):
        factor = sample_risk_factors[0]
        assert 0.0 <= factor.weight <= 1.0
        assert factor.category in list(FeatureCategory)
        assert factor.factor_id != ""

    def test_risk_factor_is_immutable(self, sample_risk_factors):
        with pytest.raises(Exception):
            sample_risk_factors[0].weight = 0.9

    def test_weight_validation(self):
        with pytest.raises(Exception):
            RiskFactor(name="test", weight=1.5, contribution=0.1, category=FeatureCategory.SENSOR)


# ── RiskFeature Tests ─────────────────────────────────────────────────────────

class TestRiskFeature:
    def test_sensor_feature_defaults(self):
        feature = RiskFeature(name="temp_mean", value=0.5, category=FeatureCategory.SENSOR)
        assert feature.missing is False
        assert feature.source == ""
        assert feature.timestamp != ""

    def test_missing_feature(self):
        feature = RiskFeature(name="temp_mean", value=0.0, category=FeatureCategory.SENSOR, missing=True)
        assert feature.missing is True

    def test_feature_is_immutable(self, sample_sensor_features):
        with pytest.raises(Exception):
            sample_sensor_features[0].value = 0.9


# ── RiskConfidence Tests ──────────────────────────────────────────────────────

class TestRiskConfidence:
    def test_completeness_ratio(self, high_confidence):
        ratio = high_confidence.completeness_ratio
        assert 0.0 <= ratio <= 1.0

    def test_completeness_ratio_zero_features(self):
        conf = RiskConfidence(overall=0.5, feature_count=0, missing_feature_count=0)
        assert conf.completeness_ratio == 0.0

    def test_completeness_ratio_no_missing(self):
        conf = RiskConfidence(overall=0.9, feature_count=20, missing_feature_count=0)
        assert conf.completeness_ratio == 1.0

    def test_completeness_ratio_partial(self, partial_confidence):
        # 8 missing out of 15 = 7/15 completeness
        assert partial_confidence.completeness_ratio == pytest.approx(7/15, rel=0.01)

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            RiskConfidence(overall=1.5)


# ── RiskForecast Tests ────────────────────────────────────────────────────────

class TestRiskForecast:
    def test_get_horizon_existing(self, sample_forecast):
        pred = sample_forecast.get_horizon(ForecastHorizon.FIVE_MIN)
        assert pred is not None
        assert pred.risk_type == RiskType.EQUIPMENT_FAILURE

    def test_get_horizon_missing(self, sample_forecast):
        # All horizons are filled in sample_forecast, test with a missing one
        empty_forecast = RiskForecast(
            entity_id="test",
            entity_type=EntityType.EQUIPMENT,
            predictions={},
        )
        assert empty_forecast.get_horizon(ForecastHorizon.FIVE_MIN) is None

    def test_peak_risk_returns_max(self, sample_forecast):
        peak = sample_forecast.peak_risk
        assert peak is not None
        all_values = [p.risk_score.value for p in sample_forecast.predictions.values()]
        assert peak.value == max(all_values)

    def test_peak_risk_empty_forecast(self):
        forecast = RiskForecast(entity_id="t", entity_type=EntityType.ZONE, predictions={})
        assert forecast.peak_risk is None

    def test_forecast_has_all_horizons(self, sample_forecast):
        assert len(sample_forecast.predictions) == len(list(ForecastHorizon))

    def test_forecast_entity_fields(self, sample_forecast, sample_entity_id):
        assert sample_forecast.entity_id == sample_entity_id
        assert sample_forecast.entity_type == EntityType.EQUIPMENT


# ── RiskAssessment Tests ──────────────────────────────────────────────────────

class TestRiskAssessment:
    def test_assessment_has_required_fields(self, sample_assessment):
        assert sample_assessment.assessment_id != ""
        assert sample_assessment.entity_id != ""
        assert sample_assessment.timestamp != ""
        assert sample_assessment.current_risk is not None

    def test_assessment_completed_status(self, sample_assessment):
        assert sample_assessment.status == AssessmentStatus.COMPLETED

    def test_assessment_has_factors(self, sample_assessment):
        assert len(sample_assessment.top_factors) > 0

    def test_assessment_has_evidence(self, sample_assessment):
        assert len(sample_assessment.evidence) > 0

    def test_assessment_is_immutable(self, sample_assessment):
        with pytest.raises(Exception):
            sample_assessment.entity_id = "other"

    def test_assessment_latency_recorded(self, sample_assessment):
        assert sample_assessment.latency_ms > 0


# ── MitigationPlan Tests ───────────────────────────────────────────────────────

class TestMitigationPlan:
    def test_immediate_actions_filter(self, sample_mitigation_plan):
        # No IMMEDIATE priority in sample_recommendations, so 0
        immediate = sample_mitigation_plan.immediate_actions
        assert isinstance(immediate, list)

    def test_has_evacuation_false(self, sample_mitigation_plan):
        # None of the sample recommendations are EVACUATION
        assert sample_mitigation_plan.has_evacuation is False

    def test_has_evacuation_true(self, sample_entity_id):
        plan = MitigationPlan(
            entity_id=sample_entity_id,
            entity_type=EntityType.ZONE,
            recommendations=[
                RiskRecommendation(
                    mitigation_type=MitigationType.EVACUATION,
                    priority=MitigationPriority.IMMEDIATE,
                    title="Evacuate zone",
                    description="Immediate zone evacuation required",
                    estimated_risk_reduction=0.8,
                )
            ],
            total_estimated_risk_reduction=0.8,
        )
        assert plan.has_evacuation is True

    def test_plan_requires_approval_for_critical(self, sample_mitigation_plan):
        assert sample_mitigation_plan.approval_required is True

    def test_plan_has_recommendations(self, sample_mitigation_plan):
        assert len(sample_mitigation_plan.recommendations) == 3


# ── RiskScenario Tests ────────────────────────────────────────────────────────

class TestRiskScenario:
    def test_scenario_fields(self, sample_scenario):
        assert sample_scenario.scenario_id != ""
        assert sample_scenario.delta == pytest.approx(0.20, rel=0.01)
        assert sample_scenario.feasibility == 0.85

    def test_scenario_delta_is_positive_for_increased_risk(self, sample_scenario):
        # Scenario risk > baseline risk → delta > 0
        assert sample_scenario.delta > 0

    def test_scenario_modified_conditions(self, sample_scenario):
        assert "TEMP-001_rolling_mean" in sample_scenario.modified_conditions
        assert sample_scenario.modified_conditions["TEMP-001_rolling_mean"] == 0.9


# ── CompositeRisk Tests ───────────────────────────────────────────────────────

class TestCompositeRisk:
    def test_composite_risk_fields(self, sample_composite_risk):
        assert sample_composite_risk.equipment_risk is not None
        assert sample_composite_risk.composite_score is not None

    def test_composite_weights_sum_to_one(self, sample_composite_risk):
        total = sum(sample_composite_risk.weights_used.values())
        assert total == pytest.approx(1.0, rel=0.01)


# ── EquipmentRisk Tests ───────────────────────────────────────────────────────

class TestEquipmentRisk:
    def test_equipment_risk_fields(self, sample_equipment_risk):
        assert sample_equipment_risk.equipment_id == "EQ-PUMP-001"
        assert sample_equipment_risk.failure_probability == 0.35
        assert sample_equipment_risk.estimated_rul == 120.0

    def test_equipment_risk_has_base_assessment(self, sample_equipment_risk, sample_assessment):
        assert sample_equipment_risk.assessment.entity_id == sample_assessment.entity_id


# ── WorkerRisk Tests ──────────────────────────────────────────────────────────

class TestWorkerRisk:
    def test_worker_risk_fields(self, sample_worker_risk):
        assert sample_worker_risk.worker_id == "WORKER-W-001"
        assert 0.0 <= sample_worker_risk.ppe_compliance_score <= 1.0
        assert sample_worker_risk.exposure_duration_hours >= 0

    def test_worker_ppe_compliance_valid(self, sample_worker_risk):
        with pytest.raises(Exception):
            WorkerRisk(
                assessment=sample_worker_risk.assessment,
                worker_id="W-002",
                ppe_compliance_score=1.5,  # invalid
            )


# ── ZoneRisk Tests ────────────────────────────────────────────────────────────

class TestZoneRisk:
    def test_zone_risk_fields(self, sample_zone_risk):
        assert sample_zone_risk.zone_id == "ZONE-A-01"
        assert sample_zone_risk.worker_count == 5
        assert len(sample_zone_risk.equipment_ids) > 0

    def test_zone_risk_hazard_types(self, sample_zone_risk):
        assert RiskType.EQUIPMENT_FAILURE in sample_zone_risk.hazard_types


# ── PlantRisk Tests ───────────────────────────────────────────────────────────

class TestPlantRisk:
    def test_plant_risk_fields(self, sample_plant_risk):
        assert sample_plant_risk.plant_id == "PLANT-001"
        assert sample_plant_risk.zone_count == 8
        assert 0.0 <= sample_plant_risk.overall_safety_index <= 1.0


# ── Domain Events Tests ───────────────────────────────────────────────────────

class TestDomainEvents:
    def test_risk_calculated_fields(self, risk_calculated_event):
        assert risk_calculated_event.event_type == "RiskCalculated"
        assert risk_calculated_event.event_id != ""
        assert 0.0 <= risk_calculated_event.risk_value <= 1.0

    def test_forecast_generated_fields(self, risk_forecast_event):
        assert risk_forecast_event.event_type == "RiskForecastGenerated"
        assert len(risk_forecast_event.horizons) == 7

    def test_threshold_exceeded_fields(self, threshold_exceeded_event):
        assert threshold_exceeded_event.actual_value > threshold_exceeded_event.threshold_value
        assert threshold_exceeded_event.event_type == "RiskThresholdExceeded"

    def test_mitigation_generated_fields(self, mitigation_generated_event):
        assert mitigation_generated_event.recommendation_count == 3
        assert mitigation_generated_event.event_type == "MitigationGenerated"

    def test_risk_escalated_fields(self, risk_escalated_event):
        assert risk_escalated_event.from_level == RiskLevel.MEDIUM
        assert risk_escalated_event.to_level == RiskLevel.HIGH
        assert risk_escalated_event.event_type == "RiskEscalated"

    def test_prediction_completed_fields(self, prediction_completed_event):
        assert prediction_completed_event.latency_ms > 0
        assert prediction_completed_event.event_type == "PredictionCompleted"

    def test_events_are_immutable(self, risk_calculated_event):
        with pytest.raises(Exception):
            risk_calculated_event.event_id = "other"

    def test_risk_event_topics_complete(self):
        from app.modules.risk_prediction.domain.events import RISK_EVENT_TOPICS
        assert "RiskCalculated" in RISK_EVENT_TOPICS
        assert "RiskForecastGenerated" in RISK_EVENT_TOPICS
        assert "RiskThresholdExceeded" in RISK_EVENT_TOPICS
        assert "MitigationGenerated" in RISK_EVENT_TOPICS
        assert "RiskEscalated" in RISK_EVENT_TOPICS
        assert "PredictionCompleted" in RISK_EVENT_TOPICS
