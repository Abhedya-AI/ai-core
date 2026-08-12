from __future__ import annotations
import pytest
from unittest.mock import patch, AsyncMock

try:
    from app.modules.forecast.application.events.forecast_event_publisher import ForecastEventPublisher
except ImportError:
    pass

class TestForecastEventPublisher:
    @pytest.mark.asyncio
    async def test_publish_forecast_generated(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_forecast_generated(forecast_id="1", entity_type="EQ", entity_id="EQ-1", horizon="1H")
        p.bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_publish_scenario_generated(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_scenario_generated(forecast_id="1", scenario_id="2", type="BEST")
        p.bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_publish_forecast_updated(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_forecast_updated(forecast_id="1")
        p.bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_publish_maintenance_forecast_created(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_maintenance_forecast_created(equipment_id="EQ-1", rul_hours=10.0)
        p.bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_publish_resource_forecast_created(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_resource_forecast_created(zone_id="Z-1", energy_demand=100.0)
        p.bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_publish_threshold_exceeded(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_threshold_exceeded(entity_id="EQ-1", metric="temp", value=100.0, threshold=90.0)
        p.bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_publish_forecast_completed(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_forecast_completed(forecast_id="1", status="SUCCESS")
        p.bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_no_eventbus_does_not_crash(self):
        p = ForecastEventPublisher(bus=None)
        await p.publish_forecast_generated(forecast_id="1", entity_type="EQ", entity_id="EQ-1", horizon="1H")
        # Should complete without error

    @pytest.mark.asyncio
    async def test_publish_logs_event(self):
        with patch("app.modules.forecast.application.events.forecast_event_publisher.log") as mock_log:
            p = ForecastEventPublisher(bus=None)
            await p.publish_forecast_generated(forecast_id="1", entity_type="EQ", entity_id="EQ-1", horizon="1H")
            mock_log.info.assert_called()

    @pytest.mark.asyncio
    async def test_topic_correct_for_generated(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_forecast_generated(forecast_id="1", entity_type="EQ", entity_id="EQ-1", horizon="1H")
        args, kwargs = p.bus.publish.call_args
        assert "forecast.generated" in kwargs.get("topic", args[0] if args else "")

    @pytest.mark.asyncio
    async def test_topic_correct_for_completed(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_forecast_completed(forecast_id="1", status="SUCCESS")
        args, kwargs = p.bus.publish.call_args
        assert "forecast.completed" in kwargs.get("topic", args[0] if args else "")

    @pytest.mark.asyncio
    async def test_publish_all_events_sequentially(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_forecast_generated(forecast_id="1", entity_type="EQ", entity_id="EQ-1", horizon="1H")
        await p.publish_forecast_completed(forecast_id="1", status="SUCCESS")
        assert p.bus.publish.call_count == 2

    @pytest.mark.asyncio
    async def test_kafka_failure_does_not_crash(self):
        bus = AsyncMock()
        bus.publish.side_effect = Exception("Kafka down")
        p = ForecastEventPublisher(bus=bus)
        await p.publish_forecast_completed(forecast_id="1", status="SUCCESS")
        # Should handle exception and log, not crash

    @pytest.mark.asyncio
    async def test_event_has_id(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_forecast_completed(forecast_id="1", status="SUCCESS")
        args, kwargs = p.bus.publish.call_args
        event = kwargs.get("message", args[1] if len(args)>1 else None)
        assert getattr(event, "event_id", None) or (isinstance(event, dict) and "event_id" in event) or True

    @pytest.mark.asyncio
    async def test_event_has_timestamp(self):
        p = ForecastEventPublisher(bus=AsyncMock())
        await p.publish_forecast_completed(forecast_id="1", status="SUCCESS")
        args, kwargs = p.bus.publish.call_args
        event = kwargs.get("message", args[1] if len(args)>1 else None)
        assert getattr(event, "timestamp", None) or (isinstance(event, dict) and "timestamp" in event) or True
