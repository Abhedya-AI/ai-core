from __future__ import annotations
import pytest

try:
    from app.modules.forecast.application.resource_forecasting.worker_availability import WorkerAvailabilityForecaster
    from app.modules.forecast.application.resource_forecasting.equipment_utilization import EquipmentUtilizationForecaster
    from app.modules.forecast.application.resource_forecasting.energy_demand import EnergyDemandForecaster
except ImportError:
    pass

class TestWorkerAvailabilityForecaster:
    @pytest.mark.asyncio
    async def test_available_workers_bounded(self):
        f = WorkerAvailabilityForecaster()
        res = await f.forecast(total_workers=100, horizon_hours=24)
        assert all(0 <= w <= 100 for w in res["available_workers"])

    @pytest.mark.asyncio
    async def test_fatigue_risk_increases_over_time(self):
        f = WorkerAvailabilityForecaster()
        res = await f.forecast(total_workers=100, horizon_hours=12)
        assert res["fatigue_risk"][-1] >= res["fatigue_risk"][0]

    @pytest.mark.asyncio
    async def test_shift_changes_detected(self):
        f = WorkerAvailabilityForecaster()
        res = await f.forecast(total_workers=100, horizon_hours=24)
        assert "shift_changes" in res

    @pytest.mark.asyncio
    async def test_medical_readiness_bounded(self):
        f = WorkerAvailabilityForecaster()
        res = await f.forecast(total_workers=100, horizon_hours=24)
        assert 0 <= res["medical_readiness"] <= 1

    @pytest.mark.asyncio
    async def test_safety_personnel_demand_proportional(self):
        f = WorkerAvailabilityForecaster()
        res1 = await f.forecast(total_workers=100, horizon_hours=24)
        res2 = await f.forecast(total_workers=200, horizon_hours=24)
        assert res2["safety_personnel_needed"] >= res1["safety_personnel_needed"]

class TestEquipmentUtilizationForecaster:
    @pytest.mark.asyncio
    async def test_utilization_bounded(self):
        f = EquipmentUtilizationForecaster()
        res = await f.forecast(equipment_count=10, horizon_hours=24)
        assert all(0 <= u <= 1.0 for u in res["utilization_rates"])

    @pytest.mark.asyncio
    async def test_low_health_reduces_availability(self):
        f = EquipmentUtilizationForecaster()
        res = await f.forecast(equipment_count=10, horizon_hours=24, average_health=0.2)
        assert np.mean(res["utilization_rates"]) < 0.5

    @pytest.mark.asyncio
    async def test_bottleneck_identified(self):
        f = EquipmentUtilizationForecaster()
        res = await f.forecast(equipment_count=10, horizon_hours=24)
        assert "bottlenecks" in res

    @pytest.mark.asyncio
    async def test_availability_probability_bounded(self):
        f = EquipmentUtilizationForecaster()
        res = await f.forecast(equipment_count=10, horizon_hours=24)
        assert 0 <= res["availability_probability"] <= 1

class TestEnergyDemandForecaster:
    @pytest.mark.asyncio
    async def test_power_consumption_positive(self):
        f = EnergyDemandForecaster()
        res = await f.forecast(horizon_hours=24)
        assert all(p >= 0 for p in res["power_consumption"])

    @pytest.mark.asyncio
    async def test_water_usage_positive(self):
        f = EnergyDemandForecaster()
        res = await f.forecast(horizon_hours=24)
        assert all(w >= 0 for w in res["water_usage"])

    @pytest.mark.asyncio
    async def test_fuel_demand_positive(self):
        f = EnergyDemandForecaster()
        res = await f.forecast(horizon_hours=24)
        assert all(f >= 0 for f in res["fuel_demand"])

    @pytest.mark.asyncio
    async def test_peak_demand_hours_identified(self):
        f = EnergyDemandForecaster()
        res = await f.forecast(horizon_hours=24)
        assert "peak_hours" in res

    @pytest.mark.asyncio
    async def test_efficiency_score_bounded(self):
        f = EnergyDemandForecaster()
        res = await f.forecast(horizon_hours=24)
        assert 0 <= res["efficiency_score"] <= 1

    @pytest.mark.asyncio
    async def test_higher_utilization_more_energy(self):
        f = EnergyDemandForecaster()
        res1 = await f.forecast(horizon_hours=24, utilization=0.5)
        res2 = await f.forecast(horizon_hours=24, utilization=0.9)
        assert sum(res2["power_consumption"]) > sum(res1["power_consumption"])
