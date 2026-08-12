from __future__ import annotations

import asyncio
from app.core.logging import get_logger

log = get_logger(__name__)

class HazardEventPublisher:
    def __init__(self) -> None:
        self._event_bus = None
        try:
            from app.core.events.event_bus import EventBus
            self._event_bus = EventBus()
        except Exception:
            pass

    def _publish(self, event) -> None:
        if self._event_bus:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._event_bus.publish(event))
                else:
                    loop.run_until_complete(self._event_bus.publish(event))
            except Exception as exc:
                log.warning(f"Event publish failed: {exc}")

    async def publish_hazard_detected(self, data: dict) -> None:
        self._publish({"event_name": "HazardDetected", "data": data})

    async def publish_propagation_updated(self, data: dict) -> None:
        self._publish({"event_name": "PropagationUpdated", "data": data})

    async def publish_exposure_assessed(self, data: dict) -> None:
        self._publish({"event_name": "ExposureAssessed", "data": data})

    async def publish_containment_plan_generated(self, data: dict) -> None:
        self._publish({"event_name": "ContainmentPlanGenerated", "data": data})

    async def publish_evacuation_required(self, data: dict) -> None:
        self._publish({"event_name": "EvacuationRequired", "data": data})

    async def publish_simulation_completed(self, data: dict) -> None:
        self._publish({"event_name": "SimulationCompleted", "data": data})

    async def publish_recommendations_generated(self, data: dict) -> None:
        self._publish({"event_name": "RecommendationsGenerated", "data": data})

    async def publish_cascade_risk_identified(self, data: dict) -> None:
        self._publish({"event_name": "CascadeRiskIdentified", "data": data})

    async def publish_hazard_contained(self, data: dict) -> None:
        self._publish({"event_name": "HazardContained", "data": data})
