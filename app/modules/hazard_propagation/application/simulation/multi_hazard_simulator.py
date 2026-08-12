from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

class MultiHazardSimulator:
    def __init__(self, what_if_simulator=None) -> None:
        self.what_if_simulator = what_if_simulator

    async def simulate_multiple_hazards(self, hazard_scenarios: list[dict], interaction_matrix: dict | None = None) -> dict:
        if not self.what_if_simulator:
            from .what_if_simulator import WhatIfSimulator
            self.what_if_simulator = WhatIfSimulator()
            
        results = []
        combined = {}
        
        for sc in hazard_scenarios:
            res = await self.what_if_simulator.simulate(sc)
            results.append(res)
            for n, val in res.get("result_nodes", {}).items():
                if n in combined:
                    combined[n] = self.compute_hazard_interaction(combined[n], val, 0.2)
                else:
                    combined[n] = val
                    
        points = self.identify_interaction_points(results)
        peak = max(combined.values()) if combined else 0.0
        
        return {
            "combined_result_nodes": combined,
            "hazard_results": results,
            "interaction_points": points,
            "peak_combined_intensity": float(peak)
        }

    def compute_hazard_interaction(self, hazard_a_intensity: float, hazard_b_intensity: float, interaction_factor: float) -> float:
        res = max(hazard_a_intensity, hazard_b_intensity) + interaction_factor * hazard_a_intensity * hazard_b_intensity
        return max(0.0, min(1.0, float(res)))

    def identify_interaction_points(self, hazard_results: list[dict]) -> list[dict]:
        all_nodes = set()
        for r in hazard_results:
            all_nodes.update(r.get("result_nodes", {}).keys())
            
        points = []
        for n in all_nodes:
            hazards = []
            vals = []
            for r in hazard_results:
                v = r.get("result_nodes", {}).get(n, 0.0)
                if v > 0.1:
                    hazards.append(r.get("scenario_name", "UNKNOWN"))
                    vals.append(v)
            if len(hazards) >= 2:
                points.append({
                    "node_id": n,
                    "hazard_types": hazards,
                    "combined_intensity": sum(vals)
                })
        return points

    def rank_hazards_by_severity(self, hazard_results: list[dict]) -> list[dict]:
        return sorted(hazard_results, key=lambda x: max(x.get("result_nodes", {}).values(), default=0.0), reverse=True)

    def generate_multi_hazard_recommendations(self, hazard_results: list[dict], interactions: list[dict]) -> list[str]:
        recs = []
        if len(hazard_results) > 1:
            recs.append("Multiple hazards detected. Prioritize evacuation over localized containment.")
        if len(interactions) > 0:
            recs.append(f"High risk of hazard compounding at {len(interactions)} nodes. Deploy blast walls.")
        return recs
