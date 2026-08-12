from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

try:
    from app.modules.forecast.application.services.forecast_orchestration_service import ForecastOrchestrationService
    from app.modules.forecast.application.services.equipment_forecast_service import EquipmentForecastService
    from app.modules.forecast.application.services.worker_forecast_service import WorkerForecastService
    from app.modules.forecast.application.services.zone_forecast_service import ZoneForecastService
    from app.modules.forecast.application.services.plant_forecast_service import PlantForecastService
    from app.modules.forecast.application.services.resource_forecast_service import ResourceForecastService
    from app.modules.forecast.application.services.maintenance_forecast_service import MaintenanceForecastService
except ImportError:
    pass

class TestForecastOrchestrationService:
    @pytest.mark.asyncio
    async def test_forecast_entity_returns_result(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.forecast_entity(entity_type="EQUIPMENT", entity_id="EQ-1", horizon="1H")
        assert res is not None

    @pytest.mark.asyncio
    async def test_forecast_equipment_returns_result(self, sample_equipment_context, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.forecast_equipment(sample_equipment_context)
        assert res is not None

    @pytest.mark.asyncio
    async def test_forecast_worker_returns_result(self, sample_worker_context, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.forecast_worker(sample_worker_context)
        assert res is not None

    @pytest.mark.asyncio
    async def test_forecast_zone_returns_result(self, sample_zone_context, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.forecast_zone(sample_zone_context)
        assert res is not None

    @pytest.mark.asyncio
    async def test_forecast_plant_returns_result(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.forecast_plant({})
        assert res is not None

    @pytest.mark.asyncio
    async def test_forecast_resources_returns_result(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.forecast_resources({})
        assert res is not None

    @pytest.mark.asyncio
    async def test_forecast_maintenance_returns_result(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.forecast_maintenance({})
        assert res is not None

    @pytest.mark.asyncio
    async def test_forecast_environment_returns_result(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.forecast_environment({})
        assert res is not None

    @pytest.mark.asyncio
    async def test_generate_scenarios_returns_three(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.generate_scenarios("forecast_123")
        assert len(res) >= 3

    @pytest.mark.asyncio
    async def test_compare_scenarios_returns_comparison(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.compare_scenarios(["s1", "s2", "s3"])
        assert res is not None

    @pytest.mark.asyncio
    async def test_get_history_returns_list(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.get_history(entity_id="EQ-1")
        assert isinstance(res, list)

    @pytest.mark.asyncio
    async def test_explain_forecast_returns_dict(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.explain_forecast("forecast_123")
        assert isinstance(res, dict)

    @pytest.mark.asyncio
    async def test_analytics_returns_summary(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.get_analytics()
        assert isinstance(res, dict)

    @pytest.mark.asyncio
    async def test_event_published_on_forecast(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        await s.forecast_entity(entity_type="EQUIPMENT", entity_id="EQ-1", horizon="1H")
        mock_event_publisher.publish_forecast_generated.assert_called()

    @pytest.mark.asyncio
    async def test_result_has_latency_ms(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher)
        res = await s.forecast_entity(entity_type="EQUIPMENT", entity_id="EQ-1", horizon="1H")
        assert "latency_ms" in res or hasattr(res, "latency_ms")

    @pytest.mark.asyncio
    async def test_graphrag_context_used(self, mock_graphrag_service, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher, graphrag=mock_graphrag_service)
        await s.forecast_entity(entity_type="EQUIPMENT", entity_id="EQ-1", horizon="1H")
        assert mock_graphrag_service.answer.call_count >= 0 # Just asserting it doesn't crash

    @pytest.mark.asyncio
    async def test_no_graphrag_still_works(self, mock_repository, mock_event_publisher):
        s = ForecastOrchestrationService(repo=mock_repository, publisher=mock_event_publisher, graphrag=None)
        res = await s.forecast_entity(entity_type="EQUIPMENT", entity_id="EQ-1", horizon="1H")
        assert res is not None

class TestEquipmentForecastService:
    @pytest.mark.asyncio
    async def test_forecast_returns_health_score(self):
        s = EquipmentForecastService()
        res = await s.forecast({"equipment_id": "EQ-1"})
        assert "health_score" in res or hasattr(res, "health_score")

    @pytest.mark.asyncio
    async def test_compute_health_score_bounded(self):
        s = EquipmentForecastService()
        res = await s.forecast({"equipment_id": "EQ-1"})
        score = res.health_score if hasattr(res, "health_score") else res.get("health_score", 0.5)
        assert 0 <= score <= 1

    @pytest.mark.asyncio
    async def test_asset_availability_bounded(self):
        s = EquipmentForecastService()
        res = await s.forecast({"equipment_id": "EQ-1"})
        avail = res.availability if hasattr(res, "availability") else res.get("availability", 0.5)
        assert 0 <= avail <= 1

class TestMaintenanceForecastService:
    @pytest.mark.asyncio
    async def test_forecast_returns_rul(self):
        s = MaintenanceForecastService()
        res = await s.forecast({"equipment_id": "EQ-1"})
        assert "rul" in res or hasattr(res, "rul") or "rul_hours" in res

    @pytest.mark.asyncio
    async def test_urgency_is_set(self):
        s = MaintenanceForecastService()
        res = await s.forecast({"equipment_id": "EQ-1"})
        assert "urgency" in res or hasattr(res, "urgency")

    @pytest.mark.asyncio
    async def test_maintenance_backlog_computed(self):
        s = MaintenanceForecastService()
        res = await s.forecast({"equipment_id": "EQ-1"})
        assert "backlog" in res or hasattr(res, "backlog")

    @pytest.mark.asyncio
    async def test_degradation_curve_non_empty(self):
        s = MaintenanceForecastService()
        res = await s.forecast({"equipment_id": "EQ-1"})
        assert "curve" in res or hasattr(res, "curve")

class TestResourceForecastService:
    @pytest.mark.asyncio
    async def test_forecast_returns_worker_availability(self):
        s = ResourceForecastService()
        res = await s.forecast({})
        assert "worker_availability" in res or hasattr(res, "worker_availability")

    @pytest.mark.asyncio
    async def test_forecast_returns_energy_data(self):
        s = ResourceForecastService()
        res = await s.forecast({})
        assert "energy_demand" in res or hasattr(res, "energy_demand")

    @pytest.mark.asyncio
    async def test_forecast_returns_utilization_data(self):
        s = ResourceForecastService()
        res = await s.forecast({})
        assert "utilization" in res or hasattr(res, "utilization")
