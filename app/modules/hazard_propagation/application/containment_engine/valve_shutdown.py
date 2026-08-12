from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

class ValveShutdownEngine:
    def __init__(self, knowledge_service=None) -> None:
        self.knowledge_service = knowledge_service

    async def identify_isolation_valves(self, zone_id: str, pipeline_ids: list[str]) -> list[dict]:
        valves = []
        valves.append({
            "valve_id": f"V-ZONE-{zone_id}",
            "type": "ZONE_MAIN",
            "zone_id": zone_id,
            "pipeline_id": "MAIN",
            "is_remote_operated": True,
            "shutdown_time_minutes": 1.0
        })
        for pid in pipeline_ids:
            valves.append({
                "valve_id": f"V-{pid}-UP",
                "type": "ISOLATION",
                "zone_id": zone_id,
                "pipeline_id": pid,
                "is_remote_operated": True,
                "shutdown_time_minutes": 2.0
            })
            valves.append({
                "valve_id": f"V-{pid}-DN",
                "type": "ISOLATION",
                "zone_id": zone_id,
                "pipeline_id": pid,
                "is_remote_operated": False,
                "shutdown_time_minutes": 5.0
            })
        return valves

    async def generate_valve_shutdown_sequence(self, valve_ids: list[dict], hazard_type: str, urgency: str) -> list[dict]:
        remote = [v for v in valve_ids if v.get("is_remote_operated")]
        manual = [v for v in valve_ids if not v.get("is_remote_operated")]
        
        sequence = []
        step = 1
        for v in remote:
            sequence.append({
                "step": step,
                "valve_id": v.get("valve_id"),
                "action": f"Remote close valve {v.get('valve_id')}",
                "time_minutes": v.get("shutdown_time_minutes", 2.0),
                "is_remote": True,
                "safety_check": f"Confirm zero flow past {v.get('valve_id')}"
            })
            step += 1
            
        for v in manual:
            sequence.append({
                "step": step,
                "valve_id": v.get("valve_id"),
                "action": f"Manual close valve {v.get('valve_id')}",
                "time_minutes": v.get("shutdown_time_minutes", 5.0),
                "is_remote": False,
                "safety_check": f"Operator visual confirmation for {v.get('valve_id')}"
            })
            step += 1
            
        return sequence

    def compute_containment_volume(self, upstream_valves: list[dict], downstream_valves: list[dict], pipe_metadata: dict) -> float:
        d_mm = pipe_metadata.get("diameter_mm", 100.0)
        l_m = pipe_metadata.get("length_m", 50.0)
        d_m = d_mm * 0.001
        vol_m3 = (math.pi / 4.0) * (d_m ** 2) * l_m
        return float(vol_m3 * 1000.0) 
        
    def estimate_pressure_relief_time(self, volume_m3: float, pressure_bar: float, relief_valve_capacity: float) -> float:
        cap = max(0.01, relief_valve_capacity)
        return float((volume_m3 * pressure_bar) / cap)

    def generate_post_shutdown_checks(self, valve_ids: list[str]) -> list[str]:
        checks = []
        for v in valve_ids:
            checks.append(f"Verify valve {v} fully closed")
            checks.append(f"Check pressure gauge downstream of {v}")
        return checks
