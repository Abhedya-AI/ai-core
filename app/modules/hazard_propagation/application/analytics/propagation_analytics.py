from __future__ import annotations

import numpy as np
from app.core.logging import get_logger

log = get_logger(__name__)

class PropagationAnalyticsService:
    def __init__(self) -> None:
        pass

    async def compute_propagation_velocity(self, timeline_entries: list[dict]) -> dict:
        if len(timeline_entries) < 2:
            return {"mean_velocity_ms": 0.0, "max_velocity_ms": 0.0, "acceleration": 0.0}
            
        velocities = []
        for i in range(1, len(timeline_entries)):
            prev = sum(1 for v in timeline_entries[i-1].get("node_intensities", {}).values() if v > 0.05)
            curr = sum(1 for v in timeline_entries[i].get("node_intensities", {}).values() if v > 0.05)
            dt = max(1.0, timeline_entries[i].get("timestamp_offset_minutes", i) - timeline_entries[i-1].get("timestamp_offset_minutes", i-1))
            velocities.append((curr - prev) / dt)
            
        mean_v = float(np.mean(velocities))
        max_v = float(np.max(velocities))
        accel = float(velocities[-1] - velocities[0]) if len(velocities) > 1 else 0.0
        
        return {
            "mean_velocity_ms": mean_v,
            "max_velocity_ms": max_v,
            "acceleration": accel
        }

    async def compute_affected_area_growth(self, timeline_entries: list[dict]) -> dict:
        if not timeline_entries:
            return {"growth_rate_per_minute": 0.0, "peak_affected_count": 0, "time_to_peak_minutes": 0.0}
            
        counts = []
        times = []
        for i, t in enumerate(timeline_entries):
            count = sum(1 for v in t.get("node_intensities", {}).values() if v > 0.05)
            counts.append(count)
            times.append(t.get("timestamp_offset_minutes", i))
            
        peak_c = max(counts)
        peak_idx = counts.index(peak_c)
        peak_t = times[peak_idx]
        
        growth = peak_c / max(1.0, peak_t) if peak_t > 0 else 0.0
        
        return {
            "growth_rate_per_minute": float(growth),
            "peak_affected_count": peak_c,
            "time_to_peak_minutes": float(peak_t)
        }

    async def compute_containment_effectiveness(self, before_state: dict, after_state: dict) -> dict:
        b_ints = before_state.get("node_intensities", {})
        a_ints = after_state.get("node_intensities", {})
        
        b_sum = sum(b_ints.values())
        a_sum = sum(a_ints.values())
        
        eff = ((b_sum - a_sum) / max(0.01, b_sum)) * 100.0 if b_sum > 0 else 0.0
        
        b_nodes = set(n for n, v in b_ints.items() if v > 0.05)
        a_nodes = set(n for n, v in a_ints.items() if v > 0.05)
        
        contained = len(b_nodes - a_nodes)
        residual = len(a_nodes)
        
        return {
            "effectiveness_pct": float(max(0.0, min(100.0, eff))),
            "nodes_contained": contained,
            "nodes_residual_risk": residual
        }

    async def compute_exposure_trends(self, exposure_history: list[dict]) -> dict:
        if not exposure_history:
            return {"trend_direction": "NONE", "mean_exposure": 0.0, "peak_exposure": 0.0, "improving": True}
            
        scores = [h.get("exposure_score", 0.0) for h in exposure_history]
        mean_exp = float(np.mean(scores))
        peak_exp = float(np.max(scores))
        
        if len(scores) < 2:
            return {"trend_direction": "NONE", "mean_exposure": mean_exp, "peak_exposure": peak_exp, "improving": True}
            
        trend = scores[-1] - scores[0]
        direction = "WORSENING" if trend > 0.05 else "IMPROVING" if trend < -0.05 else "STABLE"
        
        return {
            "trend_direction": direction,
            "mean_exposure": mean_exp,
            "peak_exposure": peak_exp,
            "improving": direction in ("IMPROVING", "STABLE")
        }

    async def compute_cascade_risk_index(self, cascade_risks: list[dict]) -> float:
        total = sum(r.get("probability", 0.0) * r.get("impact", 0.5) for r in cascade_risks)
        return float(max(0.0, min(1.0, total)))

    async def compute_evacuation_efficiency(self, planned_time: float, actual_time: float, worker_count: int) -> dict:
        act = max(0.01, actual_time)
        eff = min(100.0, (planned_time / act) * 100.0)
        rate = worker_count / act
        return {
            "efficiency_pct": float(eff),
            "workers_per_minute": float(rate),
            "on_schedule": bool(actual_time <= planned_time)
        }

    async def generate_analytics_summary(self, propagation_id: str, timeline: list[dict], exposure_data: list[dict], containment_data: dict) -> dict:
        vel = await self.compute_propagation_velocity(timeline)
        growth = await self.compute_affected_area_growth(timeline)
        exp_trends = await self.compute_exposure_trends(exposure_data)
        
        b_state = containment_data.get("before", {})
        a_state = containment_data.get("after", {})
        cont = await self.compute_containment_effectiveness(b_state, a_state)
        
        return {
            "propagation_id": propagation_id,
            "velocity": vel,
            "growth": growth,
            "exposure_trends": exp_trends,
            "containment_stats": cont
        }
