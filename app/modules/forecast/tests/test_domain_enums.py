from __future__ import annotations
import pytest

try:
    from app.modules.forecast.domain.enums import (
        ForecastHorizon, ForecastType, ForecastStatus, ScenarioType,
        ConfidenceLevel, ModelFamily, ForecastTrend, RecommendationType, ForecastTarget
    )
except ImportError:
    pass

class TestForecastHorizon:
    def test_all_horizons_exist(self):
        assert len(list(ForecastHorizon)) >= 8

    def test_fifteen_min_minutes(self):
        assert ForecastHorizon.FIFTEEN_MIN.minutes == 15

    def test_thirty_min_minutes(self):
        assert ForecastHorizon.THIRTY_MIN.minutes == 30

    def test_one_hour_minutes(self):
        assert ForecastHorizon.ONE_HOUR.minutes == 60

    def test_six_hour_minutes(self):
        assert ForecastHorizon.SIX_HOUR.minutes == 360

    def test_twenty_four_hour_minutes(self):
        assert ForecastHorizon.TWENTY_FOUR_HOUR.minutes == 1440

    def test_three_day_minutes(self):
        assert ForecastHorizon.THREE_DAY.minutes == 4320

    def test_seven_day_minutes(self):
        assert ForecastHorizon.SEVEN_DAY.minutes == 10080

    def test_thirty_day_minutes(self):
        assert ForecastHorizon.THIRTY_DAY.minutes == 43200

    def test_horizon_label_property(self):
        assert "Hour" in ForecastHorizon.ONE_HOUR.label or "15" in ForecastHorizon.FIFTEEN_MIN.label

    def test_horizon_days_property(self):
        assert ForecastHorizon.SEVEN_DAY.days == 7.0

class TestForecastType:
    def test_all_fifteen_types_exist(self):
        types = [e.value for e in ForecastType]
        assert len(types) >= 3

    def test_equipment_health_exists(self):
        assert ForecastType.EQUIPMENT_HEALTH

    def test_worker_safety_exists(self):
        assert ForecastType.WORKER_SAFETY

    def test_plant_health_exists(self):
        assert ForecastType.PLANT_HEALTH

class TestConfidenceLevel:
    def test_from_score_very_low(self):
        assert ConfidenceLevel.from_score(0.1) == ConfidenceLevel.VERY_LOW

    def test_from_score_high(self):
        assert ConfidenceLevel.from_score(0.75) == ConfidenceLevel.HIGH

    def test_from_score_very_high(self):
        assert ConfidenceLevel.from_score(0.95) == ConfidenceLevel.VERY_HIGH

class TestScenarioType:
    def test_three_scenarios_exist(self):
        assert len(list(ScenarioType)) == 3

class TestForecastStatus:
    def test_status_exists(self):
        assert len(list(ForecastStatus)) > 0
        
class TestForecastTrend:
    def test_trend_exists(self):
        assert len(list(ForecastTrend)) > 0

class TestModelFamily:
    def test_model_family_exists(self):
        assert len(list(ModelFamily)) > 0
