from __future__ import annotations
import pytest
from datetime import datetime

try:
    from app.modules.forecast.domain.events import (
        ForecastDomainEvent, ForecastGenerated, ScenarioGenerated, ForecastUpdated,
        MaintenanceForecastCreated, ResourceForecastCreated, ForecastThresholdExceeded,
        ForecastCompleted, FORECAST_EVENT_TOPICS
    )
except ImportError:
    pass

class TestForecastDomainEvent:
    def test_event_has_id(self):
        e = ForecastDomainEvent()
        assert e.event_id is not None

    def test_event_has_timestamp(self):
        e = ForecastDomainEvent()
        assert e.timestamp is not None

    def test_event_is_frozen(self):
        e = ForecastDomainEvent()
        with pytest.raises(Exception):
            e.event_id = "new-id"

    def test_source_is_forecast(self):
        e = ForecastDomainEvent()
        assert e.source == "forecast"

class TestForecastGenerated:
    def test_event_type_correct(self):
        e = ForecastGenerated(forecast_id="123", entity_type="EQUIPMENT", entity_id="EQ-1", horizon="1H")
        assert e.event_type == "ForecastGenerated"

    def test_topic_in_topics_dict(self):
        e = ForecastGenerated(forecast_id="123", entity_type="EQUIPMENT", entity_id="EQ-1", horizon="1H")
        assert "forecast.generated" in FORECAST_EVENT_TOPICS.values()

    def test_required_fields(self):
        e = ForecastGenerated(forecast_id="123", entity_type="EQUIPMENT", entity_id="EQ-1", horizon="1H")
        assert e.forecast_id == "123"
        assert e.entity_id == "EQ-1"
        assert e.horizon == "1H"

class TestFORECAST_EVENT_TOPICS:
    def test_all_events_have_topics(self):
        assert "FORECAST_GENERATED" in FORECAST_EVENT_TOPICS

    def test_topic_count(self):
        assert len(FORECAST_EVENT_TOPICS) >= 7

    def test_topic_format(self):
        for topic in FORECAST_EVENT_TOPICS.values():
            assert topic.startswith("forecast.")

class TestScenarioGenerated:
    def test_scenario_generated_type(self):
        e = ScenarioGenerated(forecast_id="1", scenario_id="2", type="BEST_CASE")
        assert e.event_type == "ScenarioGenerated"

class TestForecastUpdated:
    def test_forecast_updated_type(self):
        e = ForecastUpdated(forecast_id="1")
        assert e.event_type == "ForecastUpdated"

class TestMaintenanceForecastCreated:
    def test_maintenance_forecast_created(self):
        e = MaintenanceForecastCreated(equipment_id="EQ-1", rul_hours=10.0)
        assert e.event_type == "MaintenanceForecastCreated"
        assert e.equipment_id == "EQ-1"

class TestResourceForecastCreated:
    def test_resource_forecast_created(self):
        e = ResourceForecastCreated(zone_id="Z-1", energy_demand=100.0)
        assert e.event_type == "ResourceForecastCreated"
        assert e.energy_demand == 100.0

class TestForecastThresholdExceeded:
    def test_threshold_exceeded(self):
        e = ForecastThresholdExceeded(entity_id="E-1", metric="temp", value=100.0, threshold=90.0)
        assert e.event_type == "ForecastThresholdExceeded"
        assert e.metric == "temp"
        assert e.value > e.threshold

class TestForecastCompleted:
    def test_forecast_completed(self):
        e = ForecastCompleted(forecast_id="1", status="SUCCESS")
        assert e.event_type == "ForecastCompleted"
        assert e.status == "SUCCESS"

    def test_forecast_completed_latency(self):
        e = ForecastCompleted(forecast_id="1", status="SUCCESS", latency_ms=150)
        assert e.latency_ms == 150
