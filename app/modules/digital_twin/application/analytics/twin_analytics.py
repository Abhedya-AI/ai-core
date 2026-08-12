from __future__ import annotations
import numpy as np
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class TwinAnalyticsService:
    def __init__(self):
        pass

    async def compute_twin_health_summary(self, twin_state: dict[str, Any]) -> dict[str, Any]:
        zones = twin_state.get("zone_states", {})
        equipment = twin_state.get("equipment_states", {})
        workers = twin_state.get("worker_states", {})
        hazards = twin_state.get("hazard_states", {})

        z_healths = [z.get("health_score", 1.0) for z in zones.values()]
        e_healths = [e.get("health_score", 1.0) for e in equipment.values()]
        
        overall = float(np.mean(z_healths + e_healths)) if (z_healths or e_healths) else 1.0
        
        return {
            "overall_health_score": overall,
            "zones_healthy": len([z for z in z_healths if z > 0.8]),
            "zones_degraded": len([z for z in z_healths if 0.5 <= z <= 0.8]),
            "zones_critical": len([z for z in z_healths if z < 0.5]),
            "equipment_healthy": len([e for e in e_healths if e > 0.8]),
            "equipment_degraded": len([e for e in e_healths if 0.5 <= e <= 0.8]),
            "equipment_critical": len([e for e in e_healths if e < 0.5]),
            "workers_safe": len([w for w in workers.values() if w.get("exposure_risk_score", 0.0) < 0.3]),
            "workers_at_risk": len([w for w in workers.values() if w.get("exposure_risk_score", 0.0) >= 0.3]),
            "active_hazards": len([h for h in hazards.values() if h.get("is_active", True)]),
            "sync_health": 1.0
        }

    async def compute_state_trends(self, state_history: list[dict[str, Any]], entity_id: str) -> dict[str, Any]:
        if len(state_history) < 2:
            return {"trend_direction": "STABLE", "health_slope": 0.0, "risk_slope": 0.0, "volatility": 0.0, "anomaly_count": 0}
            
        healths = [s.get("health_score", 1.0) for s in state_history]
        risks = [s.get("risk_score", 0.0) for s in state_history]
        x = np.arange(len(healths))
        
        h_slope = float(np.polyfit(x, healths, 1)[0])
        r_slope = float(np.polyfit(x, risks, 1)[0])
        volatility = float(np.std(healths))
        
        direction = "STABLE"
        if h_slope < -0.05:
            direction = "DEGRADING"
        elif h_slope > 0.05:
            direction = "IMPROVING"
            
        return {
            "trend_direction": direction,
            "health_slope": h_slope,
            "risk_slope": r_slope,
            "volatility": volatility,
            "anomaly_count": 0
        }

    async def compute_sync_performance(self, sync_history: list[dict[str, Any]]) -> dict[str, Any]:
        if not sync_history:
            return {"avg_latency_ms": 0.0, "p95_latency_ms": 0.0, "success_rate": 1.0, "slowest_source": "N/A", "fastest_source": "N/A"}
            
        latencies = [s.get("latency_ms", 0.0) for s in sync_history]
        successes = len([s for s in sync_history if s.get("status") == "SUCCESS"])
        
        return {
            "avg_latency_ms": float(np.mean(latencies)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
            "success_rate": successes / len(sync_history),
            "slowest_source": "unknown",
            "fastest_source": "unknown"
        }

    async def compute_simulation_effectiveness(self, simulations: list[dict[str, Any]]) -> dict[str, Any]:
        if not simulations:
            return {"total_runs": 0, "success_rate": 0.0, "avg_confidence": 0.0, "most_common_type": "N/A", "avg_latency_ms": 0.0}
            
        successes = len([s for s in simulations if s.get("status") == "SUCCESS"])
        confidences = [s.get("confidence", 0.0) for s in simulations]
        latencies = [s.get("latency_ms", 0.0) for s in simulations]
        
        types = [s.get("simulation_type", "UNKNOWN") for s in simulations]
        most_common = max(set(types), key=types.count) if types else "N/A"
        
        return {
            "total_runs": len(simulations),
            "success_rate": successes / len(simulations),
            "avg_confidence": float(np.mean(confidences)),
            "most_common_type": most_common,
            "avg_latency_ms": float(np.mean(latencies))
        }

    async def compute_optimization_impact(self, optimizations: list[dict[str, Any]]) -> dict[str, Any]:
        if not optimizations:
            return {"total_runs": 0, "avg_improvement_pct": 0.0, "best_target": "N/A", "total_value_generated": 0.0}
            
        improvements = [o.get("improvement_score", 0.0) for o in optimizations]
        targets = [o.get("target", "UNKNOWN") for o in optimizations]
        best_target = max(set(targets), key=targets.count) if targets else "N/A"
        
        return {
            "total_runs": len(optimizations),
            "avg_improvement_pct": float(np.mean(improvements)) * 100,
            "best_target": best_target,
            "total_value_generated": sum(improvements) * 1000 # dummy value
        }

    async def compute_entity_risk_matrix(self, twin_state: dict[str, Any]) -> dict[str, Any]:
        zones = twin_state.get("zone_states", {})
        equipment = twin_state.get("equipment_states", {})
        workers = twin_state.get("worker_states", {})
        
        matrix = {}
        for z_id, z_data in zones.items():
            eq_count = len([e for e in equipment.values() if e.get("zone_id") == z_id])
            w_count = len([w for w in workers.values() if w.get("current_zone") == z_id])
            
            matrix[z_id] = {
                "equipment_count": eq_count,
                "worker_count": w_count,
                "risk_score": z_data.get("risk_score", 0.0),
                "health_score": z_data.get("health_score", 1.0),
                "status": "NORMAL" if z_data.get("risk_score", 0.0) < 0.5 else "HIGH_RISK"
            }
            
        return dict(sorted(matrix.items(), key=lambda item: item[1]["risk_score"], reverse=True))

    async def compute_plant_kpis(self, twin_state: dict[str, Any]) -> dict[str, Any]:
        equipment = twin_state.get("equipment_states", {})
        metrics = twin_state.get("metrics", {})
        
        availability = float(np.mean([e.get("availability", 0.9) for e in equipment.values()])) if equipment else 0.9
        performance = metrics.get("performance", 0.85)
        quality = metrics.get("quality", 0.95)
        
        oee = availability * performance * quality
        
        return {
            "oee": oee,
            "mtbf": metrics.get("mtbf_hours", 500.0),
            "mttr": metrics.get("mttr_hours", 4.0),
            "safety_index": metrics.get("safety_index", 0.98),
            "compliance_rate": metrics.get("compliance_rate", 1.0),
            "energy_efficiency": metrics.get("energy_efficiency", 0.85)
        }
