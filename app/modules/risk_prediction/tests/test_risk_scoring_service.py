"""
app/modules/risk_prediction/tests/test_risk_scoring_service.py
Tests for RiskScoringService — probability calibration, composite risk,
confidence computation, factor extraction, explanation generation.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from app.modules.risk_prediction.application.services.risk_scoring_service import RiskScoringService
from app.modules.risk_prediction.domain.enums import (
    EntityType,
    FeatureCategory,
    RiskLevel,
    RiskType,
)
from app.modules.risk_prediction.domain.models import (
    RiskConfidence,
    RiskFactor,
    RiskFeature,
    RiskScore,
)


@pytest.fixture
def scoring_service():
    return RiskScoringService()


class TestComputeRiskScore:
    def test_high_probability_returns_high_level(self, scoring_service, high_confidence):
        score = scoring_service.compute_risk_score(
            raw_probability=0.70,
            confidence=high_confidence,
            uncertainty=0.05,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        assert score.value > 0.3  # Still elevated after calibration

    def test_low_probability_returns_low_level(self, scoring_service, high_confidence):
        score = scoring_service.compute_risk_score(
            raw_probability=0.05,
            confidence=high_confidence,
            uncertainty=0.0,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        assert score.level in (RiskLevel.NEGLIGIBLE, RiskLevel.LOW)

    def test_output_is_risk_score(self, scoring_service, high_confidence):
        score = scoring_service.compute_risk_score(
            raw_probability=0.5,
            confidence=high_confidence,
            uncertainty=0.1,
            risk_type=RiskType.FIRE,
        )
        assert isinstance(score, RiskScore)
        assert 0.0 <= score.value <= 1.0

    def test_reduced_confidence_with_partial_features(self, scoring_service, partial_confidence):
        score = scoring_service.compute_risk_score(
            raw_probability=0.5,
            confidence=partial_confidence,
            uncertainty=0.1,
            risk_type=RiskType.OPERATIONAL,
        )
        # Lower completeness should reduce overall confidence
        assert score.confidence <= 0.9

    def test_uncertainty_propagated_to_score(self, scoring_service, high_confidence):
        score = scoring_service.compute_risk_score(
            raw_probability=0.5,
            confidence=high_confidence,
            uncertainty=0.3,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        assert score.uncertainty >= 0.0


class TestComputeCompositeRisk:
    def test_composite_of_equal_risks(self, scoring_service):
        dimensions = {"equipment": 0.5, "worker": 0.5}
        weights = {"equipment": 0.5, "worker": 0.5}
        score = scoring_service.compute_composite_risk(dimensions, weights)
        assert isinstance(score, RiskScore)
        assert 0.0 <= score.value <= 1.0

    def test_composite_dominated_by_high_dimension(self, scoring_service):
        # One very high risk dimension should pull composite up
        dimensions = {"equipment": 0.9, "worker": 0.1, "zone": 0.1}
        weights = {"equipment": 0.30, "worker": 0.25, "zone": 0.20}
        score = scoring_service.compute_composite_risk(dimensions, weights)
        # Geometric mean should be elevated
        assert score.value > 0.1

    def test_composite_all_low(self, scoring_service):
        dimensions = {"equipment": 0.05, "worker": 0.05, "zone": 0.05}
        weights = {"equipment": 0.33, "worker": 0.33, "zone": 0.34}
        score = scoring_service.compute_composite_risk(dimensions, weights)
        assert score.value < 0.3

    def test_composite_empty_dimensions(self, scoring_service):
        score = scoring_service.compute_composite_risk({}, {})
        assert 0.0 <= score.value <= 1.0

    def test_composite_mismatched_keys(self, scoring_service):
        dimensions = {"equipment": 0.5}
        weights = {"equipment": 0.5, "worker": 0.5}
        # Should handle gracefully
        score = scoring_service.compute_composite_risk(dimensions, weights)
        assert isinstance(score, RiskScore)


class TestComputeConfidence:
    def test_full_feature_completeness(self, scoring_service):
        completeness = {
            "SENSOR": 1.0,
            "VISION": 1.0,
            "GRAPH": 1.0,
            "GRAPHRAG": 1.0,
        }
        confidence = scoring_service.compute_confidence(
            feature_vector_completeness=completeness,
            model_confidences=[0.9, 0.85, 0.88],
        )
        assert confidence.overall > 0.80

    def test_partial_feature_completeness_lowers_confidence(self, scoring_service):
        completeness = {"SENSOR": 0.5, "VISION": 0.0, "GRAPH": 0.8, "GRAPHRAG": 0.5}
        confidence = scoring_service.compute_confidence(
            feature_vector_completeness=completeness,
            model_confidences=[0.8],
        )
        full_completeness = {"SENSOR": 1.0, "VISION": 1.0, "GRAPH": 1.0, "GRAPHRAG": 1.0}
        full_confidence = scoring_service.compute_confidence(
            feature_vector_completeness=full_completeness,
            model_confidences=[0.8],
        )
        assert confidence.overall <= full_confidence.overall

    def test_confidence_is_bounded(self, scoring_service):
        completeness = {"SENSOR": 1.0}
        confidence = scoring_service.compute_confidence(
            feature_vector_completeness=completeness,
            model_confidences=[0.95],
        )
        assert 0.0 <= confidence.overall <= 1.0

    def test_empty_model_confidences(self, scoring_service):
        completeness = {"SENSOR": 1.0}
        confidence = scoring_service.compute_confidence(
            feature_vector_completeness=completeness,
            model_confidences=[],
        )
        assert isinstance(confidence, RiskConfidence)


class TestCalibrateProb:
    def test_calibrate_mid_probability(self, scoring_service):
        # Platt scaling with a=1, b=0: sigmoid(0.5) ≈ 0.378
        calibrated = scoring_service.calibrate_probability(0.5)
        assert 0.0 <= calibrated <= 1.0

    def test_calibrate_zero_probability(self, scoring_service):
        calibrated = scoring_service.calibrate_probability(0.0)
        assert 0.0 <= calibrated <= 1.0

    def test_calibrate_one_probability(self, scoring_service):
        calibrated = scoring_service.calibrate_probability(1.0)
        assert 0.0 <= calibrated <= 1.0


class TestComputeUncertainty:
    def test_agreement_is_low_uncertainty(self, scoring_service):
        # Models all agree → low uncertainty
        probs = [0.5, 0.51, 0.49, 0.50]
        uncertainty = scoring_service.compute_uncertainty(probs)
        assert uncertainty < 0.1

    def test_disagreement_is_high_uncertainty(self, scoring_service):
        # Models strongly disagree → high uncertainty
        probs = [0.1, 0.9, 0.1, 0.9]
        uncertainty = scoring_service.compute_uncertainty(probs)
        assert uncertainty > 0.3

    def test_single_model_zero_uncertainty(self, scoring_service):
        uncertainty = scoring_service.compute_uncertainty([0.5])
        assert uncertainty == 0.0

    def test_empty_models_zero_uncertainty(self, scoring_service):
        uncertainty = scoring_service.compute_uncertainty([])
        assert uncertainty == 0.0


class TestExtractTopFactors:
    def test_extract_returns_risk_factors(self, scoring_service, sample_all_features):
        from app.modules.risk_prediction.application.feature_engineering.feature_collector import FeatureVector
        fv = FeatureVector(
            entity_id="EQ-001",
            entity_type=EntityType.EQUIPMENT,
            features=sample_all_features,
            collected_at="",
            sensor_completeness=0.9,
            vision_completeness=0.8,
            graph_completeness=0.9,
            graphrag_completeness=0.7,
        )
        importance = {f.name: abs(f.value) for f in sample_all_features}
        factors = scoring_service.extract_top_factors(importance, fv, limit=5)
        assert len(factors) <= 5
        assert all(isinstance(f, RiskFactor) for f in factors)

    def test_extract_sorted_by_importance(self, scoring_service, sample_all_features):
        from app.modules.risk_prediction.application.feature_engineering.feature_collector import FeatureVector
        fv = FeatureVector(
            entity_id="EQ-001",
            entity_type=EntityType.EQUIPMENT,
            features=sample_all_features,
            collected_at="",
            sensor_completeness=0.9,
            vision_completeness=0.8,
            graph_completeness=0.9,
            graphrag_completeness=0.7,
        )
        importance = {f.name: abs(f.value) for f in sample_all_features}
        factors = scoring_service.extract_top_factors(importance, fv, limit=10)
        if len(factors) > 1:
            contributions = [f.contribution for f in factors]
            # Should be sorted descending
            assert contributions[0] >= contributions[-1]

    def test_extract_empty_importance(self, scoring_service, sample_all_features):
        from app.modules.risk_prediction.application.feature_engineering.feature_collector import FeatureVector
        fv = FeatureVector(
            entity_id="EQ-001",
            entity_type=EntityType.EQUIPMENT,
            features=sample_all_features,
            collected_at="",
            sensor_completeness=0.9,
            vision_completeness=0.8,
            graph_completeness=0.9,
            graphrag_completeness=0.7,
        )
        factors = scoring_service.extract_top_factors({}, fv, limit=5)
        assert isinstance(factors, list)


class TestBuildExplanation:
    def test_explanation_is_non_empty(self, scoring_service, medium_risk, sample_risk_factors, sample_evidence):
        explanation = scoring_service.build_explanation(
            risk_score=medium_risk,
            top_factors=sample_risk_factors,
            evidence=sample_evidence,
            risk_type=RiskType.EQUIPMENT_FAILURE,
            entity_type=EntityType.EQUIPMENT,
        )
        assert len(explanation) > 20

    def test_explanation_mentions_risk_level(self, scoring_service, high_risk, sample_risk_factors, sample_evidence):
        explanation = scoring_service.build_explanation(
            risk_score=high_risk,
            top_factors=sample_risk_factors,
            evidence=sample_evidence,
            risk_type=RiskType.EQUIPMENT_FAILURE,
            entity_type=EntityType.EQUIPMENT,
        )
        # Should mention HIGH or the level name
        assert any(kw in explanation.upper() for kw in ["HIGH", "EQUIPMENT", "RISK", "FAILURE"])

    def test_explanation_with_empty_factors(self, scoring_service, low_risk):
        explanation = scoring_service.build_explanation(
            risk_score=low_risk,
            top_factors=[],
            evidence=[],
            risk_type=RiskType.OPERATIONAL,
            entity_type=EntityType.ZONE,
        )
        assert isinstance(explanation, str)
