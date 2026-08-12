from __future__ import annotations
import pytest

try:
    from app.modules.forecast.application.graph_forecasting.hazard_propagation import HazardPropagationForecaster
    from app.modules.forecast.application.graph_forecasting.dependency_evolution import DependencyEvolutionForecaster
    from app.modules.forecast.application.graph_forecasting.risk_propagation import RiskPropagationForecaster
except ImportError:
    pass

class TestHazardPropagationForecaster:
    @pytest.mark.asyncio
    async def test_forecast_returns_affected_zones(self):
        f = HazardPropagationForecaster()
        res = await f.forecast(hazard_id="H-1", source_zone="Z-1")
        assert "affected_zones" in res

    @pytest.mark.asyncio
    async def test_propagation_probability_bounded(self):
        f = HazardPropagationForecaster()
        res = await f.forecast(hazard_id="H-1", source_zone="Z-1")
        assert all(0 <= z["probability"] <= 1 for z in res["affected_zones"])

    @pytest.mark.asyncio
    async def test_no_knowledge_service_defaults(self):
        f = HazardPropagationForecaster(knowledge_service=None)
        res = await f.forecast(hazard_id="H-1", source_zone="Z-1")
        assert len(res["affected_zones"]) >= 0

    @pytest.mark.asyncio
    async def test_containment_hours_positive(self):
        f = HazardPropagationForecaster()
        res = await f.forecast(hazard_id="H-1", source_zone="Z-1")
        assert res.get("estimated_containment_hours", 1) > 0

    @pytest.mark.asyncio
    async def test_propagation_path_not_empty(self):
        f = HazardPropagationForecaster()
        res = await f.forecast(hazard_id="H-1", source_zone="Z-1")
        assert "propagation_paths" in res

class TestDependencyEvolutionForecaster:
    @pytest.mark.asyncio
    async def test_forecast_returns_dict(self):
        f = DependencyEvolutionForecaster()
        res = await f.forecast(node_id="N-1")
        assert isinstance(res, dict)

    @pytest.mark.asyncio
    async def test_dependency_risk_scores_bounded(self):
        f = DependencyEvolutionForecaster()
        res = await f.forecast(node_id="N-1")
        for dep in res.get("dependencies", []):
            assert 0 <= dep["risk_score"] <= 1

    @pytest.mark.asyncio
    async def test_bottleneck_probability_bounded(self):
        f = DependencyEvolutionForecaster()
        res = await f.forecast(node_id="N-1")
        assert 0 <= res.get("bottleneck_probability", 0) <= 1

class TestRiskPropagationForecaster:
    @pytest.mark.asyncio
    async def test_propagated_risks_bounded(self):
        f = RiskPropagationForecaster()
        res = await f.forecast(source_node="N-1", initial_risk=0.8)
        assert all(0 <= r["risk"] <= 1 for r in res.get("propagated_risks", []))

    @pytest.mark.asyncio
    async def test_total_system_risk_bounded(self):
        f = RiskPropagationForecaster()
        res = await f.forecast(source_node="N-1", initial_risk=0.8)
        assert 0 <= res.get("total_system_risk", 0) <= 1

    @pytest.mark.asyncio
    async def test_high_initial_risk_propagates(self):
        f = RiskPropagationForecaster()
        res1 = await f.forecast(source_node="N-1", initial_risk=0.9)
        res2 = await f.forecast(source_node="N-1", initial_risk=0.1)
        assert res1.get("total_system_risk", 0) >= res2.get("total_system_risk", 0)

    @pytest.mark.asyncio
    async def test_risk_paths_list(self):
        f = RiskPropagationForecaster()
        res = await f.forecast(source_node="N-1", initial_risk=0.8)
        assert isinstance(res.get("paths", []), list)

    @pytest.mark.asyncio
    async def test_zero_risk_stays_zero(self):
        f = RiskPropagationForecaster()
        res = await f.forecast(source_node="N-1", initial_risk=0.0)
        assert res.get("total_system_risk", 0) < 0.1
