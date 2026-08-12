from __future__ import annotations
import pytest
import numpy as np

try:
    from app.modules.forecast.application.analytics.forecast_analytics import ForecastAnalyticsService
except ImportError:
    pass

class TestForecastAnalyticsService:
    @pytest.mark.asyncio
    async def test_accuracy_metrics_mae(self):
        a = ForecastAnalyticsService()
        metrics = await a.compute_accuracy(actual=[1.0, 2.0], predicted=[1.1, 1.9])
        assert abs(metrics["mae"] - 0.1) < 0.01

    @pytest.mark.asyncio
    async def test_accuracy_metrics_rmse(self):
        a = ForecastAnalyticsService()
        metrics = await a.compute_accuracy(actual=[1.0, 2.0], predicted=[1.1, 1.9])
        assert metrics["rmse"] > 0

    @pytest.mark.asyncio
    async def test_accuracy_metrics_r_squared(self):
        a = ForecastAnalyticsService()
        metrics = await a.compute_accuracy(actual=[1.0, 2.0, 3.0], predicted=[1.1, 1.9, 3.1])
        assert 0 <= metrics["r_squared"] <= 1

    @pytest.mark.asyncio
    async def test_perfect_prediction_metrics(self):
        a = ForecastAnalyticsService()
        metrics = await a.compute_accuracy(actual=[1.0, 2.0], predicted=[1.0, 2.0])
        assert metrics["mae"] == 0.0
        assert metrics["rmse"] == 0.0
        assert metrics["r_squared"] == 1.0

    @pytest.mark.asyncio
    async def test_forecast_drift_detection(self):
        a = ForecastAnalyticsService()
        drift = await a.detect_drift(history=[1.0, 1.0], recent=[2.0, 2.0])
        assert drift["is_drifting"] is True

    @pytest.mark.asyncio
    async def test_drift_direction_identified(self):
        a = ForecastAnalyticsService()
        drift = await a.detect_drift(history=[1.0, 1.0], recent=[2.0, 2.0])
        assert drift["direction"] == "UP"

    @pytest.mark.asyncio
    async def test_confidence_trends(self):
        a = ForecastAnalyticsService()
        trend = await a.analyze_confidence_trend([0.9, 0.8, 0.7])
        assert trend["direction"] == "DOWN"

    @pytest.mark.asyncio
    async def test_improving_confidence_detected(self):
        a = ForecastAnalyticsService()
        trend = await a.analyze_confidence_trend([0.7, 0.8, 0.9])
        assert trend["direction"] == "UP"

    @pytest.mark.asyncio
    async def test_equipment_health_trends(self):
        a = ForecastAnalyticsService()
        trend = await a.analyze_health_trend([0.9, 0.8, 0.7])
        assert trend["is_degrading"] is True

    @pytest.mark.asyncio
    async def test_degrading_health_detected(self):
        a = ForecastAnalyticsService()
        trend = await a.analyze_health_trend([0.9, 0.5])
        assert trend["rate_of_change"] < 0

    @pytest.mark.asyncio
    async def test_zone_health_evolution(self):
        a = ForecastAnalyticsService()
        ev = await a.analyze_zone_evolution({"Z-1": [0.9, 0.8]})
        assert "Z-1" in ev

    @pytest.mark.asyncio
    async def test_plant_health_summary(self):
        a = ForecastAnalyticsService()
        summary = await a.summarize_plant_health([0.9, 0.95, 0.85])
        assert summary["average"] > 0

    @pytest.mark.asyncio
    async def test_anomaly_count_correct(self):
        a = ForecastAnalyticsService()
        count = await a.count_anomalies([1.0, 1.0, 10.0, 1.0])
        assert count > 0

    @pytest.mark.asyncio
    async def test_projection_30d_computed(self):
        a = ForecastAnalyticsService()
        proj = await a.project_30_days([1.0, 1.0])
        assert len(proj) == 30

    @pytest.mark.asyncio
    async def test_overall_trend_identified(self):
        a = ForecastAnalyticsService()
        trend = await a.get_overall_trend([1, 2, 3, 4, 5])
        assert trend == "UP"
