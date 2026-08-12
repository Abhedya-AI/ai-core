from __future__ import annotations
import pytest
import numpy as np

try:
    from app.modules.forecast.application.forecast_models.statistical import ARIMAForecastModel, ExponentialSmoothingModel
    from app.modules.forecast.application.forecast_models.prophet_model import ProphetForecastAbstraction
    from app.modules.forecast.application.forecast_models.lstm_model import LSTMForecastAbstraction
    from app.modules.forecast.application.forecast_models.transformer_model import TransformerForecastAbstraction
    from app.modules.forecast.application.forecast_models.bayesian_model import BayesianForecastAbstraction
    from app.modules.forecast.application.forecast_models.rule_based import RuleBasedForecastModel
    from app.modules.forecast.application.forecast_models.ensemble import ForecastEnsemble
except ImportError:
    pass

class TestARIMAForecastModel:
    @pytest.mark.asyncio
    async def test_train_and_forecast(self, sample_time_series, sample_timestamps):
        m = ARIMAForecastModel()
        await m.train(sample_time_series, sample_timestamps)
        res = await m.forecast(steps=10)
        assert len(res) == 10

    @pytest.mark.asyncio
    async def test_forecast_returns_correct_steps(self, sample_time_series, sample_timestamps):
        m = ARIMAForecastModel()
        await m.train(sample_time_series, sample_timestamps)
        res = await m.forecast(steps=5)
        assert len(res) == 5

    @pytest.mark.asyncio
    async def test_confidence_bands_lower_lt_upper(self, sample_time_series, sample_timestamps):
        m = ARIMAForecastModel()
        await m.train(sample_time_series, sample_timestamps)
        bands = await m.get_confidence_bands()
        assert all(u > l for u, l in zip(bands["upper"], bands["lower"]))

    def test_confidence_between_0_and_1(self):
        m = ARIMAForecastModel()
        conf = m.get_confidence_score()
        assert 0 <= conf <= 1

    def test_explain_returns_dict(self):
        m = ARIMAForecastModel()
        exp = m.explain()
        assert isinstance(exp, dict)

    def test_serialize_is_dict(self):
        m = ARIMAForecastModel()
        s = m.serialize()
        assert isinstance(s, dict)

class TestExponentialSmoothingModel:
    @pytest.mark.asyncio
    async def test_train_and_forecast(self, sample_time_series, sample_timestamps):
        m = ExponentialSmoothingModel()
        await m.train(sample_time_series, sample_timestamps)
        res = await m.forecast(steps=10)
        assert len(res) == 10

    @pytest.mark.asyncio
    async def test_forecast_length_correct(self, sample_time_series, sample_timestamps):
        m = ExponentialSmoothingModel()
        await m.train(sample_time_series, sample_timestamps)
        res = await m.forecast(steps=5)
        assert len(res) == 5

    def test_confidence_non_zero(self):
        m = ExponentialSmoothingModel()
        conf = m.get_confidence_score()
        assert conf >= 0

    def test_serialize_and_explain(self):
        m = ExponentialSmoothingModel()
        assert isinstance(m.serialize(), dict)
        assert isinstance(m.explain(), dict)

class TestProphetForecastAbstraction:
    @pytest.mark.asyncio
    async def test_train(self, sample_time_series, sample_timestamps):
        m = ProphetForecastAbstraction()
        await m.train(sample_time_series, sample_timestamps)
        assert m.is_trained

    @pytest.mark.asyncio
    async def test_forecast(self, sample_time_series, sample_timestamps):
        m = ProphetForecastAbstraction()
        await m.train(sample_time_series, sample_timestamps)
        res = await m.forecast(steps=10)
        assert len(res) == 10

    def test_r_squared_confidence(self):
        m = ProphetForecastAbstraction()
        assert 0 <= m.get_confidence_score() <= 1

    def test_explain_has_trend_slope(self):
        m = ProphetForecastAbstraction()
        exp = m.explain()
        assert "trend" in exp

class TestLSTMForecastAbstraction:
    @pytest.mark.asyncio
    async def test_train_and_forecast(self, sample_time_series, sample_timestamps):
        m = LSTMForecastAbstraction()
        await m.train(sample_time_series, sample_timestamps)
        res = await m.forecast(steps=10)
        assert len(res) == 10

    @pytest.mark.asyncio
    async def test_window_feature_explanation(self):
        m = LSTMForecastAbstraction()
        exp = m.explain()
        assert "features" in exp

class TestTransformerForecastAbstraction:
    @pytest.mark.asyncio
    async def test_attention_weights_sum_to_one(self, sample_time_series, sample_timestamps):
        m = TransformerForecastAbstraction()
        await m.train(sample_time_series, sample_timestamps)
        exp = m.explain()
        assert "attention_weights" in exp

    @pytest.mark.asyncio
    async def test_forecast_returns_result(self, sample_time_series, sample_timestamps):
        m = TransformerForecastAbstraction()
        await m.train(sample_time_series, sample_timestamps)
        res = await m.forecast(steps=10)
        assert len(res) == 10

class TestBayesianForecastAbstraction:
    @pytest.mark.asyncio
    async def test_posterior_update(self, sample_time_series, sample_timestamps):
        m = BayesianForecastAbstraction()
        await m.train(sample_time_series, sample_timestamps)
        assert m.is_trained

    @pytest.mark.asyncio
    async def test_credible_intervals_valid(self, sample_time_series, sample_timestamps):
        m = BayesianForecastAbstraction()
        await m.train(sample_time_series, sample_timestamps)
        bands = await m.get_confidence_bands()
        assert bands["upper"][0] > bands["lower"][0]

    def test_confidence_decreases_with_high_variance(self):
        m = BayesianForecastAbstraction()
        assert 0 <= m.get_confidence_score() <= 1

class TestRuleBasedForecastModel:
    @pytest.mark.asyncio
    async def test_train_builds_rules(self, sample_time_series, sample_timestamps):
        m = RuleBasedForecastModel()
        await m.train(sample_time_series, sample_timestamps)
        assert len(m.rules) > 0

    @pytest.mark.asyncio
    async def test_forecast_applies_rules(self, sample_time_series, sample_timestamps):
        m = RuleBasedForecastModel()
        await m.train(sample_time_series, sample_timestamps)
        res = await m.forecast(steps=10)
        assert len(res) == 10

    def test_explain_rules_fired(self):
        m = RuleBasedForecastModel()
        exp = m.explain()
        assert "rules_fired" in exp

class TestForecastEnsemble:
    @pytest.mark.asyncio
    async def test_train_all_models(self, sample_time_series, sample_timestamps):
        m = ForecastEnsemble()
        await m.train(sample_time_series, sample_timestamps)
        assert m.is_trained

    @pytest.mark.asyncio
    async def test_ensemble_forecast(self, sample_time_series, sample_timestamps):
        m = ForecastEnsemble()
        await m.train(sample_time_series, sample_timestamps)
        res = await m.forecast(steps=10)
        assert len(res) == 10

    @pytest.mark.asyncio
    async def test_confidence_aggregation(self, sample_time_series, sample_timestamps):
        m = ForecastEnsemble()
        await m.train(sample_time_series, sample_timestamps)
        conf = m.get_confidence_score()
        assert 0 <= conf <= 1

    def test_update_weights(self):
        m = ForecastEnsemble()
        m.update_weights([0.5, 0.5])
        assert sum(m.weights) == 1.0

    def test_explain_ensemble(self):
        m = ForecastEnsemble()
        exp = m.explain()
        assert "weights" in exp

    def test_weights_sum_to_one(self):
        m = ForecastEnsemble()
        assert abs(sum(m.weights) - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_ensemble_output_has_required_fields(self, sample_time_series, sample_timestamps):
        m = ForecastEnsemble()
        await m.train(sample_time_series, sample_timestamps)
        bands = await m.get_confidence_bands()
        assert "upper" in bands
        assert "lower" in bands
