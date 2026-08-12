from __future__ import annotations

import time
import uuid
from typing import Any
from datetime import datetime, timezone
from enum import Enum
import asyncio
import numpy as np

from app.core.logging import get_logger

log = get_logger(__name__)

class RetrainingTrigger(str, Enum):
    SCHEDULED = "SCHEDULED"
    PERFORMANCE_DROP = "PERFORMANCE_DROP"
    DATA_DRIFT = "DATA_DRIFT"
    MANUAL = "MANUAL"

class JobStatus(str, Enum):
    PENDING = "PENDING"
    RETRAINING = "RETRAINING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class RetrainingScheduler:
    def __init__(self) -> None:
        # job_id -> job dict
        self._jobs: dict[str, dict[str, Any]] = {}
        # model_id -> schedule dict
        self._schedule: dict[str, dict[str, Any]] = {}

    async def schedule(self, model_id: str, trigger: RetrainingTrigger, interval_hours: float = 24.0) -> str:
        t0 = time.perf_counter()
        schedule_id = str(uuid.uuid4())
        now_ts = datetime.now(timezone.utc).timestamp()
        next_run_ts = now_ts + (interval_hours * 3600)
        
        self._schedule[model_id] = {
            "schedule_id": schedule_id,
            "interval_hours": interval_hours,
            "next_run_at": datetime.fromtimestamp(next_run_ts, timezone.utc).isoformat(),
            "last_run_at": None,
            "trigger": trigger.value
        }
        
        log.info(f"Scheduled retraining for {model_id} every {interval_hours}h in {time.perf_counter()-t0:.4f}s")
        return schedule_id

    async def trigger_retraining(self, model_id: str, trigger: RetrainingTrigger, feedback_count: int = 0) -> dict[str, Any]:
        t0 = time.perf_counter()
        job_id = str(uuid.uuid4())
        
        job = {
            "job_id": job_id,
            "model_id": model_id,
            "status": JobStatus.RETRAINING.value,
            "trigger": trigger.value,
            "feedback_count": feedback_count,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "improvement_delta": None
        }
        self._jobs[job_id] = job
        
        # Publish event if bus exists
        try:
            from app.infrastructure.kafka.producer import EventBus
            if EventBus:
                # Mock publish
                pass
        except ImportError:
            pass
            
        # Simulate retraining work
        await asyncio.sleep(0.01) # yield control
        
        # Simulate improvement
        improvement = float(np.random.normal(0.02, 0.01))
        
        job["status"] = JobStatus.COMPLETED.value
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        job["improvement_delta"] = improvement
        
        # Update schedule if it exists
        if model_id in self._schedule:
            sch = self._schedule[model_id]
            sch["last_run_at"] = job["completed_at"]
            now_ts = datetime.now(timezone.utc).timestamp()
            next_run = now_ts + (sch["interval_hours"] * 3600)
            sch["next_run_at"] = datetime.fromtimestamp(next_run, timezone.utc).isoformat()
            
        log.info(f"Retraining completed for {model_id} (improvement: {improvement:.4f}) in {time.perf_counter()-t0:.4f}s")
        return job

    async def check_due_jobs(self) -> list[str]:
        t0 = time.perf_counter()
        due_models = []
        now_iso = datetime.now(timezone.utc).isoformat()
        
        for model_id, sch in self._schedule.items():
            if sch["next_run_at"] <= now_iso:
                due_models.append(model_id)
                
        log.debug(f"Checked due jobs in {time.perf_counter()-t0:.4f}s, found {len(due_models)}")
        return due_models

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self._jobs.get(job_id)

    async def list_jobs(self, model_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        t0 = time.perf_counter()
        results = []
        for job in self._jobs.values():
            if model_id and job["model_id"] != model_id:
                continue
            results.append(job)
            
        results.sort(key=lambda x: x["started_at"], reverse=True)
        return results[:limit]

    async def cancel_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            job = self._jobs[job_id]
            if job["status"] in [JobStatus.PENDING.value, JobStatus.RETRAINING.value]:
                job["status"] = JobStatus.CANCELLED.value
                return True
        return False

    async def get_schedule(self, model_id: str) -> dict[str, Any] | None:
        return self._schedule.get(model_id)

    async def update_schedule(self, model_id: str, interval_hours: float) -> dict[str, Any]:
        if model_id not in self._schedule:
            raise ValueError(f"No schedule found for {model_id}")
            
        sch = self._schedule[model_id]
        sch["interval_hours"] = interval_hours
        now_ts = datetime.now(timezone.utc).timestamp()
        next_run = now_ts + (interval_hours * 3600)
        sch["next_run_at"] = datetime.fromtimestamp(next_run, timezone.utc).isoformat()
        return sch

_retraining_scheduler_instance = None

def get_retraining_scheduler() -> RetrainingScheduler:
    global _retraining_scheduler_instance
    if _retraining_scheduler_instance is None:
        _retraining_scheduler_instance = RetrainingScheduler()
    return _retraining_scheduler_instance
