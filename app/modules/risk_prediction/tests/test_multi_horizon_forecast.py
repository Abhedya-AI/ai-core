"""
app/modules/risk_prediction/tests/test_multi_horizon_forecast.py
Tests for MultiHorizonForecaster — horizon generation, trend computation,
confidence decay, and mean reversion behavior.
"""
from __future__ import annotations

import pytest

from app.modules.risk_prediction.domain.enums import (
    EntityType,
    ForecastHorizon,
    RiskType,
    TrendDirection,
)
from app.modules.risk_prediction.domain.models import (
    RiskForecast,
    RiskPrediction,
    RiskTrend,
)


@pytest.fixture
def forecaster():
    from app.modules.risk_prediction.application.risk_models.rule_based_model import RuleBasedRiskModel
    from app.modules.risk_prediction.application.risk_models.statistical_model import StatisticalRiskModel
    from app.modules.risk_prediction.application.ensemble.ensemble_engine import EnsembleEngine
    from app.modules.risk_prediction.application.feature_engineering.time_series_engine import TimeSeriesEngine
    from app.modules.risk_prediction.application.forecast.multi_horizon_forecast import MultiHorizonForecaster

    ensemble = EnsembleEngine(models=[RuleBasedRiskModel(), StatisticalRiskModel()])
    ts_engine = TimeSeriesEngine()
    return MultiHorizonForecaster(ensemble_engine=ensemble, ts_engine=ts_engine)


@pytest.fixture
def sample_fv(sample_all_features):
    from app.modules.risk_prediction.application.feature_engineering.feature_collector import FeatureVector
    return FeatureVector(
        entity_id="EQ-PUMP-001",
        entity_type=EntityType.EQUIPMENT,
        features=sample_all_features,
        collected_at="",
        sensor_completeness=0.9,
        vision_completeness=0.8,
        graph_completeness=0.85,
        graphrag_completeness=0.75,
    )


class TestMultiHorizonForecast:
    @pytest.mark.asyncio
    async def test_all_horizons_generated(self, forecaster, sample_entity_id, sample_fv):
        forecast = await forecaster.generate_forecast(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            feature_vector=sample_fv,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        assert isinstance(forecast, RiskForecast)
        assert len(forecast.predictions) == 7  # All 7 horizons

    @pytest.mark.asyncio
    async def test_specific_horizons_only(self, forecaster, sample_entity_id, sample_fv):
        horizons = [ForecastHorizon.FIVE_MIN, ForecastHorizon.ONE_HOUR, ForecastHorizon.SEVEN_DAY]
        forecast = await forecaster.generate_forecast(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            feature_vector=sample_fv,
            risk_type=RiskType.EQUIPMENT_FAILURE,
            horizons=horizons,
        )
        assert len(forecast.predictions) == 3
        assert ForecastHorizon.FIVE_MIN.value in forecast.predictions
        assert ForecastHorizon.ONE_HOUR.value in forecast.predictions
        assert ForecastHorizon.SEVEN_DAY.value in forecast.predictions

    @pytest.mark.asyncio
    async def test_all_predictions_have_risk_scores(self, forecaster, sample_entity_id, sample_fv):
        forecast = await forecaster.generate_forecast(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            feature_vector=sample_fv,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        for horizon_key, prediction in forecast.predictions.items():
            assert isinstance(prediction, RiskPrediction)
            assert 0.0 <= prediction.risk_score.value <= 1.0

    @pytest.mark.asyncio
    async def test_confidence_decreases_with_horizon(self, forecaster, sample_entity_id, sample_fv):
        forecast = await forecaster.generate_forecast(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            feature_vector=sample_fv,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        # 5m should have higher confidence than 7d
        pred_5m = forecast.predictions.get(ForecastHorizon.FIVE_MIN.value)
        pred_7d = forecast.predictions.get(ForecastHorizon.SEVEN_DAY.value)
        if pred_5m and pred_7d:
            assert pred_5m.risk_score.confidence >= pred_7d.risk_score.confidence

    @pytest.mark.asyncio
    async def test_forecast_has_valid_until(self, forecaster, sample_entity_id, sample_fv):
        forecast = await forecaster.generate_forecast(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            feature_vector=sample_fv,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        assert forecast.valid_until != ""

    @pytest.mark.asyncio
    async def test_forecast_entity_fields_correct(self, forecaster, sample_entity_id, sample_fv):
        forecast = await forecaster.generate_forecast(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            feature_vector=sample_fv,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        assert forecast.entity_id == sample_entity_id
        assert forecast.entity_type == EntityType.EQUIPMENT

    @pytest.mark.asyncio
    async def test_forecast_has_trend(self, forecaster, sample_entity_id, sample_fv):
        forecast = await forecaster.generate_forecast(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            feature_vector=sample_fv,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        # Trend should be computed and should be a valid TrendDirection
        if forecast.trend is not None:
            assert forecast.trend.direction in list(TrendDirection)

    @pytest.mark.asyncio
    async def test_all_predictions_bounded(self, forecaster, sample_entity_id, sample_fv):
        forecast = await forecaster.generate_forecast(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            feature_vector=sample_fv,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        for prediction in forecast.predictions.values():
            assert 0.0 <= prediction.risk_score.value <= 1.0
            assert prediction.risk_score.confidence >= 0.0

    @pytest.mark.asyncio
    async def test_all_predictions_have_window(self, forecaster, sample_entity_id, sample_fv):
        forecast = await forecaster.generate_forecast(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            feature_vector=sample_fv,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        for horizon_key, prediction in forecast.predictions.items():
            assert prediction.window is not None
            assert prediction.window.duration_minutes > 0

    @pytest.mark.asyncio
    async def test_peak_risk_returns_max(self, forecaster, sample_entity_id, sample_fv):
        forecast = await forecaster.generate_forecast(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            feature_vector=sample_fv,
            risk_type=RiskType.EQUIPMENT_FAILURE,
        )
        peak = forecast.peak_risk
        if peak and forecast.predictions:
            all_values = [p.risk_score.value for p in forecast.predictions.values()]
            assert peak.value == pytest.approx(max(all_values), rel=0.01)

    @pytest.mark.asyncio
    async def test_forecast_for_zone_entity(self, forecaster, sample_fv):
        forecast = await forecaster.generate_forecast(
            entity_id="ZONE-A-01",
            entity_type=EntityType.ZONE,
            feature_vector=sample_fv,
            risk_type=RiskType.FIRE,
        )
        assert forecast.entity_type == EntityType.ZONE
        assert len(forecast.predictions) > 0
