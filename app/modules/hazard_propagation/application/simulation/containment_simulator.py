from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

class ContainmentSimulator:
    def __init__(self) -> None:
        pass

    async def simulate_containment(self, propagation_state: dict, containment_plan: dict, time_horizon_minutes: int = 60) -> dict:
        before = dict(propagation_state.get("node_intensities", {}))
        
        barriers = containment_plan.get("actions", [])
        graph = propagation_state.get("graph", {"nodes": [], "edges": []})
        modified_graph = self.apply_barrier_effects(graph, barriers)
        
        after = dict(before)
        for _ in range(time_horizon_minutes):
            new_after = dict(after)
            for e in modified_graph.get("edges", []):
                s, t, r = e.get("source"), e.get("target"), e.get("resistance", 0.1)
                if s in after and t in after:
                    flow = after[s] * (1.0 - r) * 0.1
                    new_after[t] = min(1.0, new_after[t] + flow)
            after = new_after
            
        eff = self.compute_containment_effectiveness(before, after)
        ttc = self.estimate_time_to_contain(containment_plan, max(before.values()) if before else 1.0)
        
        return {
            "before_containment_spread": before,
            "after_containment_spread": after,
            "containment_effectiveness": eff,
            "time_to_contain": ttc,
            "residual_risk": 1.0 - eff
        }

    def apply_barrier_effects(self, graph_state: dict, barriers: list[dict]) -> dict:
        new_state = dict(graph_state)
        edges = [dict(e) for e in new_state.get("edges", [])]
        
        for b in barriers:
            zid = b.get("zone_id")
            res = b.get("resistance_factor", 0.9)
            for e in edges:
                if e.get("source") == zid or e.get("target") == zid:
                    e["resistance"] = max(e.get("resistance", 0.0), res)
                    
        new_state["edges"] = edges
        return new_state

    def simulate_valve_shutdown(self, graph_state: dict, valve_ids: list[str], time_offset_minutes: float) -> dict:
        new_state = dict(graph_state)
        edges = []
        for e in new_state.get("edges", []):
            if e.get("pipeline_id") in valve_ids:
                pass 
            else:
                edges.append(dict(e))
        new_state["edges"] = edges
        return new_state

    def compute_containment_effectiveness(self, before: dict[str, float], after: dict[str, float]) -> float:
        sum_b = sum(before.values())
        sum_a = sum(after.values())
        if sum_b <= 0:
            return 0.0
        return float((sum_b - sum_a) / max(0.01, sum_b))

    def estimate_time_to_contain(self, containment_plan: dict, initial_intensity: float) -> float:
        actions = containment_plan.get("actions", [])
        total = sum(a.get("time_minutes", 5) for a in actions)
        return float(total * initial_intensity)
