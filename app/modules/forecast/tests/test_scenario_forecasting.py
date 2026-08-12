from __future__ import annotations
import pytest

try:
    from app.modules.forecast.application.scenario_forecasting.scenario_engine import ScenarioForecastEngine
    from app.modules.forecast.application.scenario_forecasting.uncertainty import UncertaintyQuantifier
except ImportError:
    pass

class TestScenarioForecastEngine:
    @pytest.mark.asyncio
    async def test_generates_three_scenarios(self):
        e = ScenarioForecastEngine()
        scenarios = await e.generate_scenarios(base_forecast=[1.0, 1.1, 1.2], context={})
        assert len(scenarios) == 3

    @pytest.mark.asyncio
    async def test_best_case_lower_than_expected(self):
        # Assuming lower is better for some metrics like risk
        e = ScenarioForecastEngine()
        scenarios = await e.generate_scenarios(base_forecast=[1.0, 1.0], context={"is_risk": True})
        best = next(s for s in scenarios if s.type == "BEST_CASE")
        expected = next(s for s in scenarios if s.type == "EXPECTED")
        assert sum(best.values) <= sum(expected.values)

    @pytest.mark.asyncio
    async def test_worst_case_higher_than_expected(self):
        e = ScenarioForecastEngine()
        scenarios = await e.generate_scenarios(base_forecast=[1.0, 1.0], context={"is_risk": True})
        worst = next(s for s in scenarios if s.type == "WORST_CASE")
        expected = next(s for s in scenarios if s.type == "EXPECTED")
        assert sum(worst.values) >= sum(expected.values)

    @pytest.mark.asyncio
    async def test_scenario_probabilities_sum_to_one(self):
        e = ScenarioForecastEngine()
        scenarios = await e.generate_scenarios(base_forecast=[1.0, 1.0], context={})
        probs = [s.probability for s in scenarios]
        assert abs(sum(probs) - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_scenario_spread_positive(self):
        e = ScenarioForecastEngine()
        scenarios = await e.generate_scenarios(base_forecast=[1.0, 1.0], context={})
        res = await e.compare_scenarios(scenarios)
        assert res.spread >= 0

    @pytest.mark.asyncio
    async def test_all_scenarios_have_description(self):
        e = ScenarioForecastEngine()
        scenarios = await e.generate_scenarios(base_forecast=[1.0, 1.0], context={})
        assert all(len(s.description) > 0 for s in scenarios)

    @pytest.mark.asyncio
    async def test_all_scenarios_have_conditions(self):
        e = ScenarioForecastEngine()
        scenarios = await e.generate_scenarios(base_forecast=[1.0, 1.0], context={})
        assert all(isinstance(s.conditions, list) for s in scenarios)

    @pytest.mark.asyncio
    async def test_all_scenarios_have_key_drivers(self):
        e = ScenarioForecastEngine()
        scenarios = await e.generate_scenarios(base_forecast=[1.0, 1.0], context={})
        assert all(isinstance(s.key_drivers, list) for s in scenarios)

    @pytest.mark.asyncio
    async def test_context_affects_worst_case(self):
        e = ScenarioForecastEngine()
        sc1 = await e.generate_scenarios(base_forecast=[1.0], context={"severity": "low"})
        sc2 = await e.generate_scenarios(base_forecast=[1.0], context={"severity": "high"})
        w1 = next(s for s in sc1 if s.type == "WORST_CASE").values[0]
        w2 = next(s for s in sc2 if s.type == "WORST_CASE").values[0]
        assert w2 >= w1

    @pytest.mark.asyncio
    async def test_high_confidence_reduces_spread(self):
        e = ScenarioForecastEngine()
        sc1 = await e.generate_scenarios(base_forecast=[1.0], context={"confidence": 0.1})
        sc2 = await e.generate_scenarios(base_forecast=[1.0], context={"confidence": 0.9})
        spread1 = (await e.compare_scenarios(sc1)).spread
        spread2 = (await e.compare_scenarios(sc2)).spread
        assert spread2 <= spread1

class TestUncertaintyQuantifier:
    def test_percentiles_ordered(self):
        u = UncertaintyQuantifier()
        res = u.quantify(base_value=1.0, variance=0.1)
        assert res["p5"] <= res["p25"] <= res["p50"] <= res["p75"] <= res["p95"]

    def test_p50_near_base_value(self):
        u = UncertaintyQuantifier()
        res = u.quantify(base_value=1.0, variance=0.1)
        assert abs(res["p50"] - 1.0) < 0.1

    def test_uncertainty_grows_with_horizon(self):
        u = UncertaintyQuantifier()
        res1 = u.quantify_over_time(base_values=[1.0, 1.0], base_variance=0.1)
        assert (res1[-1]["p95"] - res1[-1]["p5"]) >= (res1[0]["p95"] - res1[0]["p5"])

    def test_std_positive(self):
        u = UncertaintyQuantifier()
        res = u.quantify(base_value=1.0, variance=0.1)
        assert res["std"] > 0

    def test_uncertainty_score_bounded(self):
        u = UncertaintyQuantifier()
        res = u.quantify(base_value=1.0, variance=0.1)
        assert 0 <= res["score"] <= 1

    def test_uncertainty_sources_identified(self):
        u = UncertaintyQuantifier()
        res = u.quantify(base_value=1.0, variance=0.1)
        assert isinstance(res["sources"], list)

    def test_high_data_uncertainty_widens_bands(self):
        u = UncertaintyQuantifier()
        res1 = u.quantify(base_value=1.0, variance=0.1)
        res2 = u.quantify(base_value=1.0, variance=0.5)
        assert (res2["p95"] - res2["p5"]) > (res1["p95"] - res1["p5"])

    def test_low_uncertainty_narrow_bands(self):
        u = UncertaintyQuantifier()
        res = u.quantify(base_value=1.0, variance=0.001)
        assert (res["p95"] - res["p5"]) < 0.2

    def test_p5_lt_p25_lt_p50_lt_p75_lt_p95(self):
        u = UncertaintyQuantifier()
        res = u.quantify(base_value=10.0, variance=2.0)
        assert res["p5"] < res["p25"] < res["p50"] < res["p75"] < res["p95"]

    def test_combines_multiple_uncertainty_sources(self):
        u = UncertaintyQuantifier()
        res = u.combine_uncertainties([{"score": 0.2}, {"score": 0.4}])
        assert res["score"] >= 0.4
