from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

class WorkerPrioritizer:
    def __init__(self) -> None:
        pass

    def prioritize_workers(self, workers: list[dict], exposure_assessments: dict[str, float], zone_exposures: dict[str, float]) -> list[dict]:
        res = []
        for w in workers:
            wid = w.get("worker_id", "")
            exp_score = exposure_assessments.get(wid, 0.0)
            score = self.compute_worker_priority_score(w, exp_score)
            
            w_copy = dict(w)
            w_copy["priority_score"] = score
            res.append(w_copy)
            
        res.sort(key=lambda x: x["priority_score"], reverse=True)
        
        for i, w in enumerate(res):
            w["evacuation_priority"] = i + 1
            
        return res

    def identify_high_risk_workers(self, workers: list[dict], threshold_score: float = 0.7) -> list[dict]:
        return [w for w in workers if w.get("priority_score", 0.0) >= threshold_score]

    def compute_worker_priority_score(self, worker: dict, exposure_score: float) -> float:
        score = exposure_score
        if worker.get("is_injured"):
            score += 0.3
        if exposure_score > 0.6:
            score += 0.2
        if worker.get("role") not in ["SAFETY_OFFICER", "EMERGENCY_RESPONDER"]:
            score += 0.1
        return max(0.0, min(1.0, float(score)))

    def group_workers_for_evacuation(self, prioritized_workers: list[dict], group_size: int = 10) -> list[list[dict]]:
        groups = []
        for i in range(0, len(prioritized_workers), group_size):
            groups.append(prioritized_workers[i:i + group_size])
        return groups

    def identify_workers_requiring_assistance(self, workers: list[dict]) -> list[dict]:
        return [w for w in workers if w.get("is_injured") or w.get("has_mobility_issue")]

    def assign_evacuation_guides(self, worker_groups: list[list[dict]], available_guides: list[str]) -> dict:
        res = {g: [] for g in available_guides}
        if not available_guides:
            return res
            
        for i, grp in enumerate(worker_groups):
            guide = available_guides[i % len(available_guides)]
            res[guide].extend([w.get("worker_id") for w in grp])
            
        return res
