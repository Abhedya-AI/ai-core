from __future__ import annotations
import pytest

try:
    from app.modules.forecast.application.environmental_forecasting.gas_accumulation import GasAccumulationForecaster
    from app.modules.forecast.application.environmental_forecasting.temperature_forecast import TemperatureForecaster
    from app.modules.forecast.application.environmental_forecasting.air_quality import AirQualityForecaster
except ImportError:
    pass

class TestGasAccumulationForecaster:
    @pytest.mark.asyncio
    async def test_concentration_stays_positive(self):
        f = GasAccumulationForecaster()
        res = await f.forecast(current_ppm=10.0, horizon_hours=12)
        assert all(c >= 0 for c in res["concentration"])

    @pytest.mark.asyncio
    async def test_high_source_rate_increases_concentration(self):
        f = GasAccumulationForecaster()
        res = await f.forecast(current_ppm=10.0, source_rate=5.0, ventilation=1.0, horizon_hours=12)
        assert res["concentration"][-1] > res["concentration"][0]

    @pytest.mark.asyncio
    async def test_ventilation_reduces_concentration(self):
        f = GasAccumulationForecaster()
        res = await f.forecast(current_ppm=100.0, source_rate=0.0, ventilation=10.0, horizon_hours=12)
        assert res["concentration"][-1] < res["concentration"][0]

    @pytest.mark.asyncio
    async def test_safe_duration_positive(self):
        f = GasAccumulationForecaster()
        res = await f.forecast(current_ppm=10.0, horizon_hours=12)
        assert res["safe_duration_hours"] >= 0

    @pytest.mark.asyncio
    async def test_threshold_risk_bounded(self):
        f = GasAccumulationForecaster()
        res = await f.forecast(current_ppm=10.0, horizon_hours=12)
        assert 0 <= res["threshold_exceedance_probability"] <= 1

class TestTemperatureForecaster:
    @pytest.mark.asyncio
    async def test_temperature_forecast_generated(self):
        f = TemperatureForecaster()
        res = await f.forecast(current_temp=30.0, horizon_hours=12)
        assert len(res["temperature"]) == 12

    @pytest.mark.asyncio
    async def test_high_heat_increases_stress_risk(self):
        f = TemperatureForecaster()
        res1 = await f.forecast(current_temp=25.0, horizon_hours=12)
        res2 = await f.forecast(current_temp=45.0, horizon_hours=12)
        assert res2["heat_stress_risk"] > res1["heat_stress_risk"]

    @pytest.mark.asyncio
    async def test_cooling_requirement_positive(self):
        f = TemperatureForecaster()
        res = await f.forecast(current_temp=30.0, horizon_hours=12)
        assert res["cooling_requirement"] >= 0

    @pytest.mark.asyncio
    async def test_overheating_probability_bounded(self):
        f = TemperatureForecaster()
        res = await f.forecast(current_temp=30.0, horizon_hours=12)
        assert 0 <= res["overheating_probability"] <= 1

class TestAirQualityForecaster:
    @pytest.mark.asyncio
    async def test_aqi_forecast_generated(self):
        f = AirQualityForecaster()
        res = await f.forecast(current_aqi=50, horizon_hours=12)
        assert len(res["aqi"]) == 12

    @pytest.mark.asyncio
    async def test_health_risk_classification(self):
        f = AirQualityForecaster()
        res = await f.forecast(current_aqi=50, horizon_hours=12)
        assert "risk_level" in res

    @pytest.mark.asyncio
    async def test_ppe_recommendation_provided(self):
        f = AirQualityForecaster()
        res = await f.forecast(current_aqi=300, horizon_hours=12)
        assert "ppe_required" in res and res["ppe_required"] is True

    @pytest.mark.asyncio
    async def test_evacuation_risk_bounded(self):
        f = AirQualityForecaster()
        res = await f.forecast(current_aqi=50, horizon_hours=12)
        assert 0 <= res["evacuation_risk"] <= 1

    @pytest.mark.asyncio
    async def test_high_aqi_hazardous_classification(self):
        f = AirQualityForecaster()
        res = await f.forecast(current_aqi=400, horizon_hours=12)
        assert res["risk_level"] in ["HAZARDOUS", "CRITICAL"]

    @pytest.mark.asyncio
    async def test_low_aqi_good_classification(self):
        f = AirQualityForecaster()
        res = await f.forecast(current_aqi=20, horizon_hours=12)
        assert res["risk_level"] in ["GOOD", "SAFE", "LOW"]
