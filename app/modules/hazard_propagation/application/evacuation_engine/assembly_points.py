from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

class AssemblyPointManager:
    def __init__(self) -> None:
        pass

    def define_assembly_points(self, plant_zones: list[dict], safe_zones: list[str]) -> list[dict]:
        pts = []
        for i, z in enumerate(safe_zones):
            zone_data = next((pz for pz in plant_zones if pz.get("zone_id") == z), {})
            pts.append({
                "point_id": f"AP-{z}",
                "zone_id": z,
                "coordinates": {"x": 0, "y": 0},
                "capacity": zone_data.get("capacity", 50),
                "is_primary": (i == 0)
            })
        return pts

    def assign_workers_to_assembly_points(self, workers: list[dict], assembly_points: list[dict], worker_zone_ids: dict[str, str]) -> dict[str, list[str]]:
        assignments = {p.get("point_id"): [] for p in assembly_points}
        if not assembly_points:
            return assignments
            
        capacities = {p.get("point_id"): p.get("capacity", 50) for p in assembly_points}
        
        for w in workers:
            wid = w.get("worker_id")
            assigned = False
            for p in assembly_points:
                pid = p.get("point_id")
                if len(assignments[pid]) < capacities[pid]:
                    assignments[pid].append(wid)
                    assigned = True
                    break
            if not assigned:
                assignments[assembly_points[0].get("point_id")].append(wid)
                
        return assignments

    def compute_assembly_time(self, worker_count: int, evacuation_paths: list[dict]) -> float:
        if not evacuation_paths:
            return 15.0
        return float(max(p.get("eta_minutes", 15.0) for p in evacuation_paths))

    def check_assembly_point_capacity(self, point_id: str, assigned_workers: list[str], points: list[dict]) -> bool:
        for p in points:
            if p.get("point_id") == point_id:
                return len(assigned_workers) <= p.get("capacity", 50)
        return False

    def generate_assembly_confirmation_protocol(self, point_id: str, assigned_workers: list[str]) -> dict:
        return {
            "point_id": point_id,
            "worker_ids": assigned_workers,
            "muster_checklist": [
                "Count all workers",
                "Report missing",
                "Verify headcount with coordinator",
                "Await further instructions"
            ],
            "accountability_steps": [
                "Roll call by name",
                "Check wristbands/ID",
                "Report to incident commander"
            ]
        }
