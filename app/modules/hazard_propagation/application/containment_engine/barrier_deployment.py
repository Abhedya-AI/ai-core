from __future__ import annotations

import math
from app.core.logging import get_logger

log = get_logger(__name__)

class BarrierDeploymentEngine:
    def __init__(self) -> None:
        pass

    async def recommend_barriers(
        self, hazard_type: str, affected_zones: list[str], 
        severity: str, available_barriers: list[dict] | None = None
    ) -> list[dict]:
        recs = []
        
        for zid in affected_zones:
            if hazard_type == "FIRE":
                recs.append({"barrier_type": "FIRE_DOOR", "zone_id": zid, "priority": 1, "deployment_time_minutes": 2, "effectiveness": 0.8})
                recs.append({"barrier_type": "FIREWALL", "zone_id": zid, "priority": 2, "deployment_time_minutes": 0, "effectiveness": 0.9})
            elif hazard_type == "GAS_LEAK":
                recs.append({"barrier_type": "ISOLATION_VALVE", "zone_id": zid, "priority": 1, "deployment_time_minutes": 5, "effectiveness": 0.85})
                recs.append({"barrier_type": "VAPOUR_BARRIER", "zone_id": zid, "priority": 2, "deployment_time_minutes": 15, "effectiveness": 0.6})
            elif hazard_type == "EXPLOSION":
                recs.append({"barrier_type": "BLAST_WALL", "zone_id": zid, "priority": 1, "deployment_time_minutes": 0, "effectiveness": 0.95})
                recs.append({"barrier_type": "BLAST_CURTAIN", "zone_id": zid, "priority": 2, "deployment_time_minutes": 10, "effectiveness": 0.7})
            elif hazard_type == "CHEMICAL_SPILL":
                recs.append({"barrier_type": "CONTAINMENT_BUND", "zone_id": zid, "priority": 1, "deployment_time_minutes": 5, "effectiveness": 0.9})
                recs.append({"barrier_type": "SAFETY_VALVE", "zone_id": zid, "priority": 2, "deployment_time_minutes": 3, "effectiveness": 0.8})
            else:
                recs.append({"barrier_type": "FIRE_DOOR", "zone_id": zid, "priority": 1, "deployment_time_minutes": 2, "effectiveness": 0.5})
                
        return recs

    def compute_barrier_coverage(self, barriers: list[dict], zone_perimeter_meters: float) -> float:
        total_len = sum(b.get("length_m", 5.0) for b in barriers)
        return float(total_len / max(1.0, zone_perimeter_meters))

    def generate_barrier_deployment_plan(self, barriers: list[dict]) -> list[dict]:
        sorted_bars = sorted(barriers, key=lambda x: x.get("priority", 99))
        plan = []
        for i, b in enumerate(sorted_bars):
            plan.append({
                "task_id": f"TASK-{i+1}",
                "barrier_type": b.get("barrier_type"),
                "step": i + 1,
                "action_description": f"Deploy {b.get('barrier_type')} in zone {b.get('zone_id')}",
                "personnel_required": 2,
                "duration_minutes": b.get("deployment_time_minutes", 10)
            })
        return plan

    def estimate_total_deployment_time(self, barriers: list[dict]) -> float:
        if not barriers:
            return 0.0
        groups = {}
        for b in barriers:
            p = b.get("priority", 99)
            groups[p] = groups.get(p, 0) + b.get("deployment_time_minutes", 5)
        return float(max(groups.values()) if groups else 0.0)

    def check_barrier_compatibility(self, barrier_types: list[str], hazard_type: str) -> dict[str, bool]:
        comp = {}
        for b in barrier_types:
            if b == "FIRE_DOOR":
                comp[b] = hazard_type in ("FIRE", "SMOKE")
            elif b == "BLAST_WALL":
                comp[b] = hazard_type in ("EXPLOSION", "HIGH_PRESSURE")
            elif b == "ISOLATION_VALVE":
                comp[b] = hazard_type in ("GAS_LEAK", "STEAM_LEAK", "TOXIC_GAS")
            elif b == "CONTAINMENT_BUND":
                comp[b] = hazard_type in ("CHEMICAL_SPILL", "FLOOD")
            elif b == "VAPOUR_BARRIER":
                comp[b] = hazard_type in ("GAS_LEAK", "TOXIC_GAS")
            else:
                comp[b] = False
        return comp
