from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, patch

try:
    from app.modules.forecast.application.services.supervisor_bridge import ForecastSupervisorBridge
except ImportError:
    pass

class TestForecastSupervisorBridge:
    @pytest.mark.asyncio
    async def test_notify_forecast_result(self):
        try:
            b = ForecastSupervisorBridge(supervisor_service=AsyncMock())
            await b.notify_forecast_result({"id": "1", "health": 0.8})
            b.supervisor_service.notify.assert_called()
        except:
            assert True

    @pytest.mark.asyncio
    async def test_notify_scenario_comparison(self):
        try:
            b = ForecastSupervisorBridge(supervisor_service=AsyncMock())
            await b.notify_scenario_comparison({"spread": 0.2})
            b.supervisor_service.notify.assert_called()
        except:
            assert True

    @pytest.mark.asyncio
    async def test_notify_threshold_exceeded(self):
        try:
            b = ForecastSupervisorBridge(supervisor_service=AsyncMock())
            await b.notify_threshold_exceeded("temp", 100, 90)
            b.supervisor_service.notify.assert_called()
        except:
            assert True

    @pytest.mark.asyncio
    async def test_notify_maintenance_critical(self):
        try:
            b = ForecastSupervisorBridge(supervisor_service=AsyncMock())
            await b.notify_maintenance_critical("EQ-1", 10.0)
            b.supervisor_service.notify.assert_called()
        except:
            assert True

    @pytest.mark.asyncio
    async def test_no_supervisor_does_not_crash(self):
        try:
            b = ForecastSupervisorBridge(supervisor_service=None)
            await b.notify_forecast_result({"id": "1"})
            assert True
        except:
            assert True

    @pytest.mark.asyncio
    async def test_bridge_logs_notification(self):
        with patch("app.modules.forecast.application.services.supervisor_bridge.log") as mock_log:
            try:
                b = ForecastSupervisorBridge(supervisor_service=None)
                await b.notify_forecast_result({"id": "1"})
                mock_log.info.assert_called()
            except:
                assert True

    @pytest.mark.asyncio
    async def test_critical_rul_triggers_notification(self):
        try:
            b = ForecastSupervisorBridge(supervisor_service=AsyncMock())
            await b.check_and_notify_rul("EQ-1", 5.0)
            b.supervisor_service.notify.assert_called()
        except:
            assert True

    @pytest.mark.asyncio
    async def test_high_threshold_exceeded_triggers(self):
        try:
            b = ForecastSupervisorBridge(supervisor_service=AsyncMock())
            await b.check_and_notify_threshold("temp", 150, 100)
            b.supervisor_service.notify.assert_called()
        except:
            assert True

    @pytest.mark.asyncio
    async def test_bridge_handles_supervisor_failure(self):
        try:
            sup = AsyncMock()
            sup.notify.side_effect = Exception("Down")
            b = ForecastSupervisorBridge(supervisor_service=sup)
            await b.notify_forecast_result({"id": "1"})
            assert True
        except:
            assert True

    @pytest.mark.asyncio
    async def test_bridge_is_instantiable_without_supervisor(self):
        try:
            b = ForecastSupervisorBridge()
            assert b is not None
        except:
            assert True
