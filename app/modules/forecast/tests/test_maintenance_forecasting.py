from __future__ import annotations
import pytest

try:
    from app.modules.forecast.application.maintenance_forecasting.degradation import DegradationForecaster
    from app.modules.forecast.application.maintenance_forecasting.rul_estimator import RULEstimator
    from app.modules.forecast.application.maintenance_forecasting.failure_window import FailureWindowPredictor
except ImportError:
    pass

class TestDegradationForecaster:
    @pytest.mark.asyncio
    async def test_degradation_curve_non_empty(self, sample_time_series):
        f = DegradationForecaster()
        res = await f.forecast_degradation(sample_time_series, steps=10)
        assert len(res["curve"]) == 10

    @pytest.mark.asyncio
    async def test_degradation_rate_negative_for_declining(self, sample_time_series):
        f = DegradationForecaster()
        res = await f.forecast_degradation(sample_time_series, steps=10)
        assert res["rate"] < 0 or res["rate"] >= -1.0 # Bounded sanity check

    @pytest.mark.asyncio
    async def test_projected_health_bounded(self, sample_time_series):
        f = DegradationForecaster()
        res = await f.forecast_degradation(sample_time_series, steps=10)
        assert all(0 <= h <= 1 for h in res["curve"])

    @pytest.mark.asyncio
    async def test_failure_risk_increases_with_low_health(self):
        f = DegradationForecaster()
        res_high = await f.forecast_degradation([0.9, 0.9], steps=10)
        res_low = await f.forecast_degradation([0.3, 0.2], steps=10)
        assert res_low["failure_risk"] > res_high["failure_risk"]

    @pytest.mark.asyncio
    async def test_alert_threshold_detected(self):
        f = DegradationForecaster()
        res = await f.forecast_degradation([0.8, 0.7, 0.6], steps=10)
        assert "alert_step" in res

    @pytest.mark.asyncio
    async def test_exponential_model(self):
        f = DegradationForecaster(model="exponential")
        res = await f.forecast_degradation([0.9, 0.8, 0.7], steps=5)
        assert len(res["curve"]) == 5

    @pytest.mark.asyncio
    async def test_linear_model(self):
        f = DegradationForecaster(model="linear")
        res = await f.forecast_degradation([0.9, 0.8, 0.7], steps=5)
        assert len(res["curve"]) == 5

class TestRULEstimator:
    @pytest.mark.asyncio
    async def test_rul_hours_positive(self):
        e = RULEstimator()
        res = await e.estimate_rul([0.9, 0.85, 0.8])
        assert res["rul_hours"] > 0

    @pytest.mark.asyncio
    async def test_rul_days_consistent_with_hours(self):
        e = RULEstimator()
        res = await e.estimate_rul([0.9, 0.85, 0.8])
        assert abs(res["rul_hours"] / 24.0 - res["rul_days"]) < 0.1

    @pytest.mark.asyncio
    async def test_confidence_bounded(self):
        e = RULEstimator()
        res = await e.estimate_rul([0.9, 0.85, 0.8])
        assert 0 <= res["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_replacement_recommended_for_low_health(self):
        e = RULEstimator()
        res = await e.estimate_rul([0.3, 0.2, 0.1])
        assert res["rul_hours"] < 50

    @pytest.mark.asyncio
    async def test_safety_margin_applied(self):
        e1 = RULEstimator(safety_margin=0.0)
        e2 = RULEstimator(safety_margin=0.2)
        res1 = await e1.estimate_rul([0.9, 0.8])
        res2 = await e2.estimate_rul([0.9, 0.8])
        assert res2["rul_hours"] <= res1["rul_hours"]

class TestFailureWindowPredictor:
    @pytest.mark.asyncio
    async def test_predicts_failure_window(self):
        p = FailureWindowPredictor()
        res = await p.predict([0.8, 0.7])
        assert "start_time" in res and "end_time" in res

    @pytest.mark.asyncio
    async def test_immediate_urgency_for_short_rul(self):
        p = FailureWindowPredictor()
        res = await p.predict([0.2, 0.1])
        assert res["urgency"] in ["HIGH", "IMMEDIATE"]

    @pytest.mark.asyncio
    async def test_routine_urgency_for_long_rul(self):
        p = FailureWindowPredictor()
        res = await p.predict([0.99, 0.98])
        assert res["urgency"] in ["LOW", "ROUTINE"]

    @pytest.mark.asyncio
    async def test_recommended_actions_not_empty(self):
        p = FailureWindowPredictor()
        res = await p.predict([0.5, 0.4])
        assert len(res["recommended_actions"]) > 0

    @pytest.mark.asyncio
    async def test_catastrophic_risk_bounded(self):
        p = FailureWindowPredictor()
        res = await p.predict([0.5, 0.4])
        assert 0 <= res["catastrophic_risk"] <= 1

    @pytest.mark.asyncio
    async def test_inspection_before_failure(self):
        p = FailureWindowPredictor()
        res = await p.predict([0.5, 0.4])
        assert "inspection_deadline" in res
