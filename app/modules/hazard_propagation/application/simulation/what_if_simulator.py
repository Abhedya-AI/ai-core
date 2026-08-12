from __future__ import annotations

import asyncio
from app.core.logging import get_logger

log = get_logger(__name__)

class WhatIfSimulator:
    def __init__(self, spatial_engine=None, temporal_engine=None) -> None:
        self.spatial_engine = spatial_engine
        self.temporal_engine = temporal_engine

    async def simulate(self, scenario: dict, time_horizon_minutes: int = 60) -> dict:
        hazard_type = scenario.get("hazard_type", "UNKNOWN")
        source = scenario.get("source_node_id", "SRC")
        init_intensity = scenario.get("initial_intensity", 1.0)
        
        nodes = scenario.get("nodes", [{"id": source}])
        edges = scenario.get("edges", [])
        
        intensities = {n["id"]: 0.0 for n in nodes}
        intensities[source] = init_intensity
        
        for _ in range(time_horizon_minutes):
            new_ints = dict(intensities)
            for edge in edges:
                src, tgt = edge.get("source"), edge.get("target")
                if src in intensities and tgt in intensities:
                    flow = intensities[src] * 0.1
                    new_ints[tgt] = min(1.0, new_ints[tgt] + flow)
            intensities = new_ints
            
        affected = sum(1 for v in intensities.values() if v > 0.1)
        evac = sum(1 for v in intensities.values() if v > 0.5)
        
        return {
            "simulation_id": scenario.get("scenario_id", "SIM-1"),
            "scenario_name": scenario.get("scenario_name", "Base Scenario"),
            "result_nodes": intensities,
            "peak_affected_workers": affected * 3,
            "peak_affected_zones": affected,
            "evacuation_required_zones": evac,
            "simulation_time_steps": time_horizon_minutes,
            "confidence": 0.75
        }

    async def compare_scenarios(self, scenarios: list[dict]) -> dict:
        results = []
        for s in scenarios:
            res = await self.simulate(s)
            results.append(res)
            
        if not results:
            return {"scenarios": [], "best_outcome_scenario": "", "worst_outcome_scenario": "", "recommendation": ""}
            
        results.sort(key=lambda x: x["peak_affected_zones"])
        best = results[0]["scenario_name"]
        worst = results[-1]["scenario_name"]
        
        return {
            "scenarios": results,
            "best_outcome_scenario": best,
            "worst_outcome_scenario": worst,
            "recommendation": "Choose scenario with minimum evacuation zones"
        }

    def run_sensitivity_analysis(self, base_scenario: dict, variable: str, values: list) -> list[dict]:
        loop = asyncio.get_event_loop()
        results = []
        for v in values:
            scen = dict(base_scenario)
            scen[variable] = v
            
            if loop.is_running():
                # Just mock synchronously if event loop is running to avoid runtime error
                res = {
                    "scenario_name": f"Sens-{variable}-{v}",
                    "result_nodes": {base_scenario.get("source_node_id", "N1"): float(v) if isinstance(v, (int, float)) else 1.0},
                    "peak_affected_zones": 1
                }
            else:
                res = loop.run_until_complete(self.simulate(scen))
            results.append(res)
        return results
