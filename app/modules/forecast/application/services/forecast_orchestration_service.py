from __future__ import annotations

import logging
import time
import asyncio
import uuid
from typing import Any
from datetime import datetime, timezone

log = logging.getLogger(__name__)

from app.modules.forecast.application.repositories.forecast_repository import InMemoryForecastRepository
from app.modules.forecast.application.events.forecast_event_publisher import ForecastEventPublisher

class ForecastOrchestrationService:
    def __init__(
        self,
        repository: Any = None,
        event_publisher: Any = None,
        graphrag_service: Any = None,
        knowledge_service: Any = None,
        recommendation_engine: Any = None,
        analytics_service: Any = None,
    ):
        self.repository = repository or InMemoryForecastRepository()
        self.event_publisher = event_publisher or ForecastEventPublisher()
        self.graphrag_service = graphrag_service
        self.knowledge_service = knowledge_service
        
        try:
            from app.modules.forecast.application.recommendations.recommendation_engine import ForecastRecommendationEngine
            self.recommendation_engine = recommendation_engine or ForecastRecommendationEngine(
                graphrag_service=graphrag_service, knowledge_service=knowledge_service
            )
        except ImportError:
            self.recommendation_engine = recommendation_engine
            
        try:
            from app.modules.forecast.application.analytics.forecast_analytics import ForecastAnalyticsService
            self.analytics_service = analytics_service or ForecastAnalyticsService()
        except ImportError:
            self.analytics_service = analytics_service
            
        self._equipment_service = None
        self._worker_service = None
        self._zone_service = None
        self._plant_service = None
        self._resource_service = None
        self._maintenance_service = None

    async def _get_graphrag_context(self, entity_id: str, context: dict) -> dict:
        if self.graphrag_service:
            try:
                query = f"Get forecast context for entity {entity_id}"
                rag_context = await self.graphrag_service.answer(query)
                context["graphrag"] = rag_context
            except Exception as e:
                log.warning(f"GraphRAG failed: {e}")
        return context

    async def forecast_entity(self, entity_id: str, entity_type: str, forecast_types: list[str], horizons: list[str], context: dict) -> dict:
        t0 = time.perf_counter()
        context = await self._get_graphrag_context(entity_id, context)
        
        forecast_id = str(uuid.uuid4())
        results = {
            "forecast_id": forecast_id,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "predictions": {}
        }

        # Simplified sub-forecaster routing
        tasks = []
        if "equipment" in forecast_types:
            try:
                from app.modules.forecast.application.services.equipment_forecast_service import EquipmentForecastService
                if not self._equipment_service:
                    self._equipment_service = EquipmentForecastService()
                tasks.append(self._equipment_service.forecast(entity_id, 100.0, [], [], horizons[0] if horizons else "24h", context))
            except ImportError:
                pass
                
        # Wait for any async sub-tasks
        if tasks:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            results["predictions"]["details"] = [c for c in completed if not isinstance(c, Exception)]

        recs = []
        if self.recommendation_engine:
            try:
                recs = await self.recommendation_engine.generate_recommendations(entity_id, results)
            except Exception:
                pass
        results["recommendations"] = recs
        
        latency_ms = (time.perf_counter() - t0) * 1000
        results["latency_ms"] = latency_ms
        
        await self.repository.save_forecast(forecast_id, entity_id, "entity_multi", results)
        
        await self.event_publisher.publish_forecast_generated(
            forecast_id, entity_id, entity_type, "entity_multi", horizons[0] if horizons else "24h", 0.0, 0.8, latency_ms
        )
        return results

    async def forecast_equipment(self, equipment_id: str, context: dict) -> dict:
        t0 = time.perf_counter()
        try:
            from app.modules.forecast.application.services.equipment_forecast_service import EquipmentForecastService
            if not self._equipment_service:
                self._equipment_service = EquipmentForecastService()
            result = await self._equipment_service.forecast(equipment_id, 100.0, [], [], "24h", context)
        except ImportError:
            result = {"equipment_id": equipment_id, "status": "mock"}
            
        latency_ms = (time.perf_counter() - t0) * 1000
        result["latency_ms"] = latency_ms
        forecast_id = str(uuid.uuid4())
        result["forecast_id"] = forecast_id
        
        await self.repository.save_forecast(forecast_id, equipment_id, "equipment", result)
        await self.event_publisher.publish_forecast_generated(forecast_id, equipment_id, "equipment", "equipment", "24h", 0.0, 0.9, latency_ms)
        return result

    async def forecast_worker(self, worker_id: str, context: dict) -> dict:
        t0 = time.perf_counter()
        try:
            from app.modules.forecast.application.services.worker_forecast_service import WorkerForecastService
            if not self._worker_service:
                self._worker_service = WorkerForecastService()
            result = await self._worker_service.forecast(worker_id, 1, "zone-1", 8, 24, context)
        except ImportError:
            result = {"worker_id": worker_id}
            
        latency_ms = (time.perf_counter() - t0) * 1000
        result["latency_ms"] = latency_ms
        forecast_id = str(uuid.uuid4())
        result["forecast_id"] = forecast_id
        
        await self.repository.save_forecast(forecast_id, worker_id, "worker", result)
        await self.event_publisher.publish_forecast_generated(forecast_id, worker_id, "worker", "worker", "24h", 0.0, 0.9, latency_ms)
        return result

    async def forecast_zone(self, zone_id: str, context: dict) -> dict:
        t0 = time.perf_counter()
        try:
            from app.modules.forecast.application.services.zone_forecast_service import ZoneForecastService
            if not self._zone_service:
                self._zone_service = ZoneForecastService()
            result = await self._zone_service.forecast(zone_id, "zone_name", 10, [], {}, 24, context)
        except ImportError:
            result = {"zone_id": zone_id}
            
        latency_ms = (time.perf_counter() - t0) * 1000
        result["latency_ms"] = latency_ms
        forecast_id = str(uuid.uuid4())
        result["forecast_id"] = forecast_id
        
        await self.repository.save_forecast(forecast_id, zone_id, "zone", result)
        await self.event_publisher.publish_forecast_generated(forecast_id, zone_id, "zone", "zone", "24h", 0.0, 0.8, latency_ms)
        return result

    async def forecast_plant(self, plant_id: str, context: dict) -> dict:
        t0 = time.perf_counter()
        try:
            from app.modules.forecast.application.services.plant_forecast_service import PlantForecastService
            if not self._plant_service:
                self._plant_service = PlantForecastService(zone_service=self._zone_service)
            result = await self._plant_service.forecast(plant_id, "Plant", ["zone-1"], ["eq-1"], context)
        except ImportError:
            result = {"plant_id": plant_id}
            
        latency_ms = (time.perf_counter() - t0) * 1000
        result["latency_ms"] = latency_ms
        forecast_id = str(uuid.uuid4())
        result["forecast_id"] = forecast_id
        
        await self.repository.save_forecast(forecast_id, plant_id, "plant", result)
        await self.event_publisher.publish_forecast_generated(forecast_id, plant_id, "plant", "plant", "24h", 0.0, 0.85, latency_ms)
        return result

    async def forecast_resources(self, context: dict) -> dict:
        t0 = time.perf_counter()
        try:
            from app.modules.forecast.application.services.resource_forecast_service import ResourceForecastService
            if not self._resource_service:
                self._resource_service = ResourceForecastService()
            result = await self._resource_service.forecast(10, ["eq-1"], {}, {}, 24, context)
        except ImportError:
            result = {"resource": "summary"}
            
        latency_ms = (time.perf_counter() - t0) * 1000
        result["latency_ms"] = latency_ms
        forecast_id = str(uuid.uuid4())
        result["forecast_id"] = forecast_id
        
        await self.repository.save_forecast(forecast_id, "system", "resource", result)
        await self.event_publisher.publish_resource_forecast_created(["worker", "equipment"], "24h", result)
        return result

    async def forecast_maintenance(self, equipment_id: str, context: dict) -> dict:
        t0 = time.perf_counter()
        try:
            from app.modules.forecast.application.services.maintenance_forecast_service import MaintenanceForecastService
            if not self._maintenance_service:
                self._maintenance_service = MaintenanceForecastService()
            result = await self._maintenance_service.forecast(equipment_id, "type", 100.0, [], [], 24)
        except ImportError:
            result = {"equipment_id": equipment_id}
            
        latency_ms = (time.perf_counter() - t0) * 1000
        result["latency_ms"] = latency_ms
        forecast_id = str(uuid.uuid4())
        result["forecast_id"] = forecast_id
        
        await self.repository.save_forecast(forecast_id, equipment_id, "maintenance", result)
        await self.event_publisher.publish_maintenance_forecast_created(equipment_id, result.get("rul_hours", 0.0), result.get("urgency", "LOW"), result.get("failure_probability", 0.0))
        return result

    async def forecast_environment(self, zone_id: str, context: dict) -> dict:
        t0 = time.perf_counter()
        result = {"zone_id": zone_id, "type": "environmental"}
        latency_ms = (time.perf_counter() - t0) * 1000
        result["latency_ms"] = latency_ms
        forecast_id = str(uuid.uuid4())
        result["forecast_id"] = forecast_id
        await self.repository.save_forecast(forecast_id, zone_id, "environmental", result)
        return result

    async def generate_scenarios(self, entity_id: str, forecast_type: str, horizon: str, context: dict) -> list[dict]:
        t0 = time.perf_counter()
        scenarios = [{"scenario_id": str(uuid.uuid4()), "entity_id": entity_id, "type": forecast_type}]
        for s in scenarios:
            await self.repository.save_scenario(s["scenario_id"], entity_id, s)
        await self.event_publisher.publish_scenario_generated(entity_id, forecast_type, horizon, len(scenarios))
        return scenarios

    async def compare_scenarios(self, entity_id: str, forecast_type: str, horizon: str, context: dict) -> dict:
        return {"entity_id": entity_id, "comparison": "mock comparison"}

    async def get_history(self, entity_id: str, forecast_type: str, limit: int, offset: int) -> list[dict]:
        return await self.repository.list_forecasts(entity_id, forecast_type, limit, offset)

    async def explain_forecast(self, forecast_id: str) -> dict:
        forecast = await self.repository.get_forecast(forecast_id)
        if not forecast:
            return {}
        return {
            "forecast_id": forecast_id,
            "methodology": "Ensemble",
            "feature_importance": {"feature1": 0.8},
            "kg_paths": [],
            "uncertainty": 0.1,
            "original_data": forecast
        }

    async def get_analytics(self, entity_id: str, entity_type: str) -> dict:
        if self.analytics_service and hasattr(self.analytics_service, 'get_entity_analytics'):
            try:
                return await self.analytics_service.get_entity_analytics(entity_id, entity_type)
            except Exception:
                pass
        return {"entity_id": entity_id, "analytics": {}}
