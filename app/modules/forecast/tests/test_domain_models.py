from __future__ import annotations
import pytest

try:
    from app.modules.forecast.domain.models import (
        ForecastConfidence, ForecastWindow, ForecastMetric, ForecastEvidence,
        Forecast, ForecastResult, ForecastScenario, ForecastComparison,
        ForecastExplanation, ForecastRecommendation, EquipmentForecast,
        WorkerForecast, ZoneForecast, PlantForecast, HazardForecast,
        EnvironmentalForecast, ResourceForecast, MaintenanceForecast, CapacityForecast
    )
    from app.modules.forecast.domain.enums import ForecastHorizon, ForecastType, ForecastTarget, ScenarioType, ForecastTrend
except ImportError:
    pass

class TestForecastConfidence:
    def test_frozen_model(self):
        c = ForecastConfidence(score=0.8)
        with pytest.raises(Exception):
            c.score = 0.9

    def test_confidence_level_property(self):
        c = ForecastConfidence(score=0.8)
        assert c.level.value == "HIGH"

    def test_is_reliable_true(self):
        c = ForecastConfidence(score=0.8)
        assert c.is_reliable()

    def test_is_reliable_false(self):
        c = ForecastConfidence(score=0.4)
        assert not c.is_reliable()

    def test_default_values(self):
        c = ForecastConfidence(score=0.5)
        assert c.score == 0.5
        assert c.factors == {}

class TestForecastWindow:
    def test_for_horizon_factory(self):
        w = ForecastWindow.for_horizon(ForecastHorizon.ONE_HOUR)
        assert w.duration_minutes == 60

    def test_duration_minutes_correct(self):
        w = ForecastWindow.for_horizon(ForecastHorizon.TWENTY_FOUR_HOUR)
        assert w.duration_minutes == 1440

    def test_window_has_start_and_end(self):
        w = ForecastWindow.for_horizon(ForecastHorizon.ONE_HOUR)
        assert w.start_time is not None
        assert w.end_time is not None

class TestForecastScenario:
    def test_scenario_creation(self):
        s = ForecastScenario(type=ScenarioType.EXPECTED, description="Expected", values=[])
        assert s.type == ScenarioType.EXPECTED

    def test_scenario_types(self):
        s = ForecastScenario(type=ScenarioType.BEST_CASE, description="Best", values=[])
        assert s.type == ScenarioType.BEST_CASE

class TestForecastComparison:
    def test_spread_computed(self):
        c = ForecastComparison(
            base_value=10.0,
            best_case_value=12.0,
            worst_case_value=8.0
        )
        assert c.spread > 0

    def test_recommended_scenario(self):
        c = ForecastComparison(
            base_value=10.0,
            best_case_value=12.0,
            worst_case_value=8.0
        )
        assert c.recommended_scenario is not None

class TestEquipmentForecast:
    def test_equipment_forecast_creation(self):
        f = EquipmentForecast(
            id="EQ-1",
            health_score=0.9,
            rul_hours=100.0,
            timestamp="2026-01-01T00:00:00Z"
        )
        assert f.id == "EQ-1"

    def test_has_health_score(self):
        f = EquipmentForecast(
            id="EQ-1",
            health_score=0.9,
            rul_hours=100.0,
            timestamp="2026-01-01T00:00:00Z"
        )
        assert f.health_score == 0.9

    def test_has_rul(self):
        f = EquipmentForecast(
            id="EQ-1",
            health_score=0.9,
            rul_hours=100.0,
            timestamp="2026-01-01T00:00:00Z"
        )
        assert f.rul_hours == 100.0

class TestMaintenanceForecast:
    def test_maintenance_forecast_creation(self):
        m = MaintenanceForecast(
            equipment_id="EQ-1",
            rul_hours=50.0,
            urgency="HIGH",
            maintenance_schedule=[]
        )
        assert m.equipment_id == "EQ-1"

    def test_has_rul_hours(self):
        m = MaintenanceForecast(
            equipment_id="EQ-1",
            rul_hours=50.0,
            urgency="HIGH",
            maintenance_schedule=[]
        )
        assert m.rul_hours == 50.0

    def test_maintenance_schedule_list(self):
        m = MaintenanceForecast(
            equipment_id="EQ-1",
            rul_hours=50.0,
            urgency="HIGH",
            maintenance_schedule=[{"task": "Oil Change"}]
        )
        assert len(m.maintenance_schedule) == 1

class TestWorkerForecast:
    def test_worker_forecast_creation(self):
        w = WorkerForecast(worker_id="W-1", fatigue_score=0.2)
        assert w.worker_id == "W-1"

class TestZoneForecast:
    def test_zone_forecast_creation(self):
        z = ZoneForecast(zone_id="Z-1", risk_level=0.1)
        assert z.zone_id == "Z-1"

class TestPlantForecast:
    def test_plant_forecast_creation(self):
        p = PlantForecast(plant_id="P-1", overall_health=0.95)
        assert p.plant_id == "P-1"

class TestHazardForecast:
    def test_hazard_forecast_creation(self):
        h = HazardForecast(hazard_type="GAS", severity=0.8)
        assert h.hazard_type == "GAS"

class TestEnvironmentalForecast:
    def test_environmental_forecast_creation(self):
        e = EnvironmentalForecast(aqi=40, temp=25.0)
        assert e.aqi == 40

class TestResourceForecast:
    def test_resource_forecast_creation(self):
        r = ResourceForecast(energy_demand=100.0, water_demand=50.0)
        assert r.energy_demand == 100.0

class TestCapacityForecast:
    def test_capacity_forecast_creation(self):
        c = CapacityForecast(throughput=1000.0)
        assert c.throughput == 1000.0

class TestForecastMetric:
    def test_metric_creation(self):
        m = ForecastMetric(name="temperature", value=30.0, unit="C")
        assert m.value == 30.0

class TestForecastEvidence:
    def test_evidence_creation(self):
        e = ForecastEvidence(source="sensor_1", weight=1.0)
        assert e.weight == 1.0

class TestForecast:
    def test_forecast_creation(self):
        f = Forecast(id="f-1", type="EQUIPMENT", entity_id="EQ-1", horizon="ONE_HOUR")
        assert f.id == "f-1"

class TestForecastResult:
    def test_forecast_result_creation(self):
        r = ForecastResult(forecast_id="f-1", predicted_values=[])
        assert r.forecast_id == "f-1"

class TestForecastExplanation:
    def test_explanation_creation(self):
        e = ForecastExplanation(summary="Things look good")
        assert e.summary == "Things look good"

class TestForecastRecommendation:
    def test_recommendation_creation(self):
        r = ForecastRecommendation(action="Check temp", priority="HIGH")
        assert r.priority == "HIGH"
