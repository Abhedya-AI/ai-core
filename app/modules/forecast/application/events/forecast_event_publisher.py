from __future__ import annotations

import logging
from typing import Any
import json
import time

log = logging.getLogger(__name__)

try:
    from app.infrastructure.kafka.producer import EventBus
except ImportError:
    EventBus = None

try:
    from app.modules.forecast.domain.events import (
        ForecastDomainEvent, ForecastGenerated, ScenarioGenerated, ForecastUpdated,
        MaintenanceForecastCreated, ResourceForecastCreated, ForecastThresholdExceeded,
        ForecastCompleted, FORECAST_EVENT_TOPICS
    )
except ImportError:
    pass

class ForecastEventPublisher:
    """Publishes forecast domain events to the message broker."""

    def __init__(self, event_bus: Any = None):
        self.event_bus = event_bus or EventBus

    async def _publish(self, event: Any) -> None:
        """Internal method to publish an event."""
        log.info(f"Publishing forecast event: {event.event_type} - {event.model_dump_json()}")
        if self.event_bus:
            try:
                topic = FORECAST_EVENT_TOPICS.get(event.event_type, "forecast.events")
                if hasattr(self.event_bus, 'publish'):
                    await self.event_bus.publish(topic, event.model_dump())
            except Exception as e:
                log.error(f"Failed to publish event {event.event_type}: {e}")

    async def publish_forecast_generated(self, forecast_id: str, entity_id: str, entity_type: str, forecast_type: str, horizon: str, value: float, confidence: float, latency_ms: float) -> None:
        try:
            event = ForecastGenerated(
                forecast_id=forecast_id,
                entity_id=entity_id,
                entity_type=entity_type,
                forecast_type=forecast_type,
                horizon=horizon,
                value=value,
                confidence=confidence,
                latency_ms=latency_ms
            )
            await self._publish(event)
        except Exception:
            pass

    async def publish_scenario_generated(self, entity_id: str, forecast_type: str, horizon: str, scenario_count: int) -> None:
        try:
            event = ScenarioGenerated(
                entity_id=entity_id,
                forecast_type=forecast_type,
                horizon=horizon,
                scenario_count=scenario_count
            )
            await self._publish(event)
        except Exception:
            pass

    async def publish_forecast_updated(self, forecast_id: str, entity_id: str, forecast_type: str, old_value: float, new_value: float) -> None:
        try:
            event = ForecastUpdated(
                forecast_id=forecast_id,
                entity_id=entity_id,
                forecast_type=forecast_type,
                old_value=old_value,
                new_value=new_value
            )
            await self._publish(event)
        except Exception:
            pass

    async def publish_maintenance_forecast_created(self, equipment_id: str, rul_hours: float, maintenance_urgency: str, failure_probability: float) -> None:
        try:
            event = MaintenanceForecastCreated(
                equipment_id=equipment_id,
                rul_hours=rul_hours,
                maintenance_urgency=maintenance_urgency,
                failure_probability=failure_probability
            )
            await self._publish(event)
        except Exception:
            pass

    async def publish_resource_forecast_created(self, resource_types: list[str], horizon: str, summary_data: dict[str, Any]) -> None:
        try:
            event = ResourceForecastCreated(
                resource_types=resource_types,
                horizon=horizon,
                summary_data=summary_data
            )
            await self._publish(event)
        except Exception:
            pass

    async def publish_threshold_exceeded(self, entity_id: str, forecast_type: str, threshold: float, actual_value: float, horizon: str) -> None:
        try:
            event = ForecastThresholdExceeded(
                entity_id=entity_id,
                forecast_type=forecast_type,
                threshold=threshold,
                actual_value=actual_value,
                horizon=horizon
            )
            await self._publish(event)
        except Exception:
            pass

    async def publish_forecast_completed(self, forecast_id: str, entity_id: str, entity_type: str, horizons_count: int, latency_ms: float, confidence: float) -> None:
        try:
            event = ForecastCompleted(
                forecast_id=forecast_id,
                entity_id=entity_id,
                entity_type=entity_type,
                horizons_count=horizons_count,
                latency_ms=latency_ms,
                confidence=confidence
            )
            await self._publish(event)
        except Exception:
            pass
