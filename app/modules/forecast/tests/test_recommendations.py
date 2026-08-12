from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock

try:
    from app.modules.forecast.application.recommendations.recommendation_engine import ForecastRecommendationEngine
except ImportError:
    pass

class TestForecastRecommendationEngine:
    @pytest.mark.asyncio
    async def test_generates_recommendations(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"health": 0.5})
        assert len(recs) > 0

    @pytest.mark.asyncio
    async def test_high_value_immediate_priority(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"health": 0.1})
        assert any(r.priority in ["HIGH", "IMMEDIATE", "CRITICAL"] for r in recs)

    @pytest.mark.asyncio
    async def test_low_value_low_priority(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"health": 0.95})
        assert all(r.priority in ["LOW", "ROUTINE", "MEDIUM"] for r in recs)

    @pytest.mark.asyncio
    async def test_each_recommendation_has_title(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"health": 0.5})
        assert all(hasattr(r, "title") and len(r.title) > 0 for r in recs)

    @pytest.mark.asyncio
    async def test_each_recommendation_has_description(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"health": 0.5})
        assert all(hasattr(r, "description") and len(r.description) > 0 for r in recs)

    @pytest.mark.asyncio
    async def test_each_recommendation_has_type(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"health": 0.5})
        assert all(hasattr(r, "type") for r in recs)

    @pytest.mark.asyncio
    async def test_graphrag_integrated_if_available(self, mock_graphrag_service):
        e = ForecastRecommendationEngine(graphrag_service=mock_graphrag_service)
        recs = await e.generate(forecast_data={"health": 0.5})
        mock_graphrag_service.answer.assert_called()
        assert len(recs) > 0

    @pytest.mark.asyncio
    async def test_no_graphrag_still_works(self):
        e = ForecastRecommendationEngine(graphrag_service=None)
        recs = await e.generate(forecast_data={"health": 0.5})
        assert len(recs) > 0

    @pytest.mark.asyncio
    async def test_equipment_health_recommendations(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"type": "EQUIPMENT", "health": 0.4})
        assert any("maintenance" in r.title.lower() or "inspect" in r.title.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_maintenance_recommendations(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"type": "MAINTENANCE", "rul": 10})
        assert len(recs) > 0

    @pytest.mark.asyncio
    async def test_worker_safety_recommendations(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"type": "WORKER_SAFETY", "fatigue": 0.9})
        assert any("rest" in r.title.lower() or "shift" in r.title.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_estimated_impact_bounded(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"health": 0.5})
        for r in recs:
            if hasattr(r, "estimated_impact"):
                assert 0 <= r.estimated_impact <= 1

    @pytest.mark.asyncio
    async def test_recommendations_are_list(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"health": 0.5})
        assert isinstance(recs, list)

    @pytest.mark.asyncio
    async def test_prioritization_is_applied(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"health": 0.1})
        # Typically the first should be highest priority
        if len(recs) > 1:
            val_map = {"CRITICAL": 4, "IMMEDIATE": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
            assert val_map.get(recs[0].priority, 0) >= val_map.get(recs[-1].priority, 0)

    @pytest.mark.asyncio
    async def test_resources_required_listed(self):
        e = ForecastRecommendationEngine()
        recs = await e.generate(forecast_data={"health": 0.5})
        for r in recs:
            assert hasattr(r, "resources_required") and isinstance(r.resources_required, list)
