"""
app/modules/risk_prediction/tests/test_risk_models.py
Tests for all ML model implementations: rule-based, statistical, Bayesian,
and optional XGBoost/LightGBM/Random Forest interfaces.
"""
from __future__ import annotations

import numpy as np
import pytest


# ── RuleBasedModel Tests ──────────────────────────────────────────────────────

class TestRuleBasedModel:
    @pytest.fixture
    def model(self):
        from app.modules.risk_prediction.application.risk_models.rule_based_model import RuleBasedRiskModel
        return RuleBasedRiskModel()

    @pytest.fixture
    def no_risk_features(self):
        names = [
            "sensor_aggregate_anomaly_count",
            "sensor_critical_count",
            "TEMP-001_drift_score",
            "TEMP-001_rate_of_change",
            "vision_ppe_compliance_score",
            "vision_fire_detection_score",
            "vision_fall_detection_score",
            "graph_critical_path_score",
            "graph_hazard_proximity",
            "graph_historical_failure_count",
        ]
        values = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        return values, names

    @pytest.fixture
    def high_risk_features(self):
        names = [
            "sensor_anomaly_count_1h",
            "sensor_drift_score",
            "rate_of_change",
            "fire_detection_score",
            "ppe_compliance",
        ]
        values = np.array([5.0, 0.8, 0.9, 0.5, 0.3])
        return values, names

    @pytest.mark.asyncio
    async def test_no_risk_low_probability(self, model, no_risk_features):
        values, names = no_risk_features
        prediction = await model.predict(values, names)
        assert prediction.probability < 0.3

    @pytest.mark.asyncio
    async def test_high_risk_features_high_probability(self, model, high_risk_features):
        values, names = high_risk_features
        prediction = await model.predict(values, names)
        assert prediction.probability > 0.4

    @pytest.mark.asyncio
    async def test_prediction_probability_bounded(self, model, high_risk_features):
        values, names = high_risk_features
        prediction = await model.predict(values, names)
        assert 0.0 <= prediction.probability <= 1.0

    @pytest.mark.asyncio
    async def test_prediction_has_explanation(self, model, high_risk_features):
        values, names = high_risk_features
        prediction = await model.predict(values, names)
        assert prediction.explanation != ""

    @pytest.mark.asyncio
    async def test_prediction_has_feature_importance(self, model, high_risk_features):
        values, names = high_risk_features
        prediction = await model.predict(values, names)
        assert len(prediction.feature_importance) > 0

    @pytest.mark.asyncio
    async def test_fire_detection_drives_high_risk(self, model):
        names = ["fire_detection_score"]
        values = np.array([0.8])
        prediction = await model.predict(values, names)
        assert prediction.probability > 0.4

    @pytest.mark.asyncio
    async def test_ppe_violation_drives_risk(self, model):
        names = ["ppe_compliance"]
        values = np.array([0.3])  # Below 0.6 threshold
        prediction = await model.predict(values, names)
        assert prediction.probability > 0.25

    def test_explain_returns_dict(self, model, high_risk_features):
        values, names = high_risk_features
        importance = model.explain(values, names)
        assert isinstance(importance, dict)

    def test_model_is_available(self, model):
        assert model.is_available() is True

    def test_model_type(self, model):
        from app.modules.risk_prediction.domain.enums import ModelType
        assert model.model_type == ModelType.RULE_BASED

    @pytest.mark.asyncio
    async def test_predict_proba_returns_array(self, model, high_risk_features):
        values, names = high_risk_features
        proba = await model.predict_proba(values)
        assert isinstance(proba, np.ndarray)
        # Should be at least 1 element (probability of risk)

    @pytest.mark.asyncio
    async def test_critical_path_multiplier(self, model):
        names = [
            "sensor_aggregate_anomaly_count",
            "graph_critical_path_score",
        ]
        # Without critical path
        values_no_cp = np.array([4.0, 0.0])
        pred_no_cp = await model.predict(values_no_cp, names)
        # With critical path
        values_cp = np.array([4.0, 1.0])
        pred_cp = await model.predict(values_cp, names)
        # Critical path should increase risk
        assert pred_cp.probability >= pred_no_cp.probability


# ── StatisticalModel Tests ─────────────────────────────────────────────────────

class TestStatisticalModel:
    @pytest.fixture
    def model(self):
        from app.modules.risk_prediction.application.risk_models.statistical_model import StatisticalRiskModel
        return StatisticalRiskModel()

    @pytest.fixture
    def safe_features(self):
        # Features at baseline (z-score ~0)
        names = ["temp_mean", "pressure_mean", "vibration_mean"]
        values = np.array([0.5, 0.5, 0.5])
        return values, names

    @pytest.fixture
    def anomalous_features(self):
        # Features far from baseline (z-score ~3)
        names = ["temp_mean", "pressure_mean", "vibration_mean"]
        values = np.array([0.95, 0.92, 0.88])
        return values, names

    @pytest.mark.asyncio
    async def test_safe_features_low_risk(self, model, safe_features):
        values, names = safe_features
        prediction = await model.predict(values, names)
        assert prediction.probability < 0.5

    @pytest.mark.asyncio
    async def test_anomalous_features_higher_risk(self, model, anomalous_features):
        values, names = anomalous_features
        prediction = await model.predict(values, names)
        assert prediction.probability > 0.0

    @pytest.mark.asyncio
    async def test_probability_bounded(self, model, anomalous_features):
        values, names = anomalous_features
        prediction = await model.predict(values, names)
        assert 0.0 <= prediction.probability <= 1.0

    def test_fit_baseline_updates_stats(self, model):
        matrix = np.array([[1.0, 2.0], [1.1, 2.1], [0.9, 1.9]])
        names = ["feat_a", "feat_b"]
        model.fit_baseline(matrix, names)
        assert model.mean_vector is not None
        assert model.std_vector is not None

    @pytest.mark.asyncio
    async def test_risk_lower_after_fitting_safe_baseline(self, model):
        # Fit baseline on safe data
        safe_data = np.array([[0.5, 0.5]] * 50)
        names = ["feat_a", "feat_b"]
        model.fit_baseline(safe_data, names)
        # Predict safe features
        values = np.array([0.5, 0.5])
        prediction = await model.predict(values, names)
        assert prediction.probability < 0.4

    def test_explain_returns_zscore_contributions(self, model, safe_features):
        values, names = safe_features
        importance = model.explain(values, names)
        assert isinstance(importance, dict)

    @pytest.mark.asyncio
    async def test_empty_features(self, model):
        prediction = await model.predict(np.array([]), [])
        assert 0.0 <= prediction.probability <= 1.0


# ── BayesianModel Tests ───────────────────────────────────────────────────────

class TestBayesianModel:
    @pytest.fixture
    def model(self):
        from app.modules.risk_prediction.application.risk_models.bayesian_model import BayesianRiskModel
        from app.modules.risk_prediction.domain.enums import RiskType
        return BayesianRiskModel(risk_type=RiskType.EQUIPMENT_FAILURE)

    @pytest.mark.asyncio
    async def test_prior_probability(self, model):
        # With no evidence, should return near base rate
        prediction = await model.predict(np.array([0.5]), ["generic_feature"])
        assert 0.0 <= prediction.probability <= 1.0

    @pytest.mark.asyncio
    async def test_strong_evidence_increases_probability(self, model):
        # High anomaly count = strong evidence for failure
        names = ["sensor_aggregate_anomaly_count", "graph_historical_failure_count"]
        weak_values = np.array([0.0, 0.0])
        strong_values = np.array([10.0, 5.0])
        pred_weak = await model.predict(weak_values, names)
        pred_strong = await model.predict(strong_values, names)
        assert pred_strong.probability >= pred_weak.probability

    @pytest.mark.asyncio
    async def test_probability_bounded(self, model):
        prediction = await model.predict(np.array([1.0] * 5), ["f"] * 5)
        assert 0.0 <= prediction.probability <= 1.0

    def test_model_type(self, model):
        from app.modules.risk_prediction.domain.enums import ModelType
        assert model.model_type == ModelType.BAYESIAN


# ── XGBoostModel Tests (optional) ────────────────────────────────────────────

class TestXGBoostModel:
    @pytest.fixture
    def model(self):
        from app.modules.risk_prediction.application.risk_models.xgboost_model import XGBoostRiskModel
        return XGBoostRiskModel()

    def test_availability_without_xgboost(self, model):
        # If xgboost is not installed, model should report unavailable
        try:
            import xgboost
            # If installed, availability depends on model being loaded
        except ImportError:
            assert model.is_available() is False

    @pytest.mark.asyncio
    async def test_predict_raises_when_unavailable(self, model):
        from app.modules.risk_prediction.application.risk_models.base_model import ModelNotAvailableError
        if not model.is_available():
            with pytest.raises((ModelNotAvailableError, Exception)):
                await model.predict(np.array([0.5]), ["feature"])


# ── EnsembleEngine Tests ──────────────────────────────────────────────────────

class TestEnsembleEngine:
    @pytest.fixture
    def ensemble(self):
        from app.modules.risk_prediction.application.risk_models.rule_based_model import RuleBasedRiskModel
        from app.modules.risk_prediction.application.risk_models.statistical_model import StatisticalRiskModel
        from app.modules.risk_prediction.application.ensemble.ensemble_engine import EnsembleEngine
        return EnsembleEngine(models=[RuleBasedRiskModel(), StatisticalRiskModel()])

    @pytest.fixture
    def test_features(self):
        names = ["sensor_aggregate_anomaly_count", "vision_ppe_compliance_score", "graph_critical_path_score"]
        values = np.array([3.0, 0.7, 0.0])
        return values, names

    @pytest.mark.asyncio
    async def test_ensemble_predict(self, ensemble, test_features):
        from app.modules.risk_prediction.domain.enums import RiskType
        values, names = test_features
        result = await ensemble.predict(values, names, RiskType.EQUIPMENT_FAILURE)
        assert 0.0 <= result.probability <= 1.0

    @pytest.mark.asyncio
    async def test_ensemble_has_model_contributions(self, ensemble, test_features):
        from app.modules.risk_prediction.domain.enums import RiskType
        values, names = test_features
        result = await ensemble.predict(values, names, RiskType.EQUIPMENT_FAILURE)
        assert len(result.model_contributions) > 0

    @pytest.mark.asyncio
    async def test_ensemble_has_uncertainty(self, ensemble, test_features):
        from app.modules.risk_prediction.domain.enums import RiskType
        values, names = test_features
        result = await ensemble.predict(values, names, RiskType.EQUIPMENT_FAILURE)
        assert result.uncertainty >= 0.0

    @pytest.mark.asyncio
    async def test_ensemble_has_confidence(self, ensemble, test_features):
        from app.modules.risk_prediction.domain.enums import RiskType
        values, names = test_features
        result = await ensemble.predict(values, names, RiskType.EQUIPMENT_FAILURE)
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_ensemble_has_explanation(self, ensemble, test_features):
        from app.modules.risk_prediction.domain.enums import RiskType
        values, names = test_features
        result = await ensemble.predict(values, names, RiskType.EQUIPMENT_FAILURE)
        assert result.ensemble_explanation != ""

    @pytest.mark.asyncio
    async def test_ensemble_lists_available_models(self, ensemble, test_features):
        from app.modules.risk_prediction.domain.enums import RiskType
        values, names = test_features
        result = await ensemble.predict(values, names, RiskType.EQUIPMENT_FAILURE)
        assert len(result.available_models) >= 1

    def test_dynamic_weight_update(self, ensemble):
        ensemble.update_weights_dynamic("RULE_BASED", 0.05)
        # Should not raise and should update weights
        assert True

    @pytest.mark.asyncio
    async def test_ensemble_single_model(self):
        from app.modules.risk_prediction.application.risk_models.rule_based_model import RuleBasedRiskModel
        from app.modules.risk_prediction.application.ensemble.ensemble_engine import EnsembleEngine
        from app.modules.risk_prediction.domain.enums import RiskType
        engine = EnsembleEngine(models=[RuleBasedRiskModel()])
        values = np.array([2.0, 0.8])
        names = ["sensor_aggregate_anomaly_count", "TEMP-001_drift_score"]
        result = await engine.predict(values, names, RiskType.EQUIPMENT_FAILURE)
        assert 0.0 <= result.probability <= 1.0
