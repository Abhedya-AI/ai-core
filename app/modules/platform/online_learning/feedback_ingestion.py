from __future__ import annotations

import time
import math
from typing import Any
from datetime import datetime, timezone
import asyncio
import numpy as np

from app.core.logging import get_logger

try:
    from app.modules.platform.online_learning.feedback_types import (
        BaseFeedback, RiskFeedback, ForecastFeedback, HazardFeedback,
        RCAFeedback, TwinFeedback, SimulationFeedback
    )
except ImportError:
    pass

log = get_logger(__name__)

class FeedbackIngestionService:
    def __init__(self) -> None:
        # model_id -> list of feedback dicts
        self._feedback_store: dict[str, list[dict[str, Any]]] = {}
        # model_id -> stats
        self._stats: dict[str, dict[str, Any]] = {}
        self._trigger_threshold = 100

    def _compute_error(self, feedback_dict: dict[str, Any]) -> float | None:
        actual = feedback_dict.get("actual")
        prediction = feedback_dict.get("prediction")
        if actual is not None and prediction is not None:
            return abs(float(actual) - float(prediction))
        return None

    async def _store_and_update_stats(self, feedback: BaseFeedback) -> str:
        f_dict = feedback.model_dump()
        mid = f_dict["model_id"]
        
        # Calculate error if possible
        if f_dict.get("error") is None:
            f_dict["error"] = self._compute_error(f_dict)
            
        if mid not in self._feedback_store:
            self._feedback_store[mid] = []
            self._stats[mid] = {
                "count": 0,
                "error_sum": 0.0,
                "last_ingested": None,
                "errors": []
            }
            
        self._feedback_store[mid].append(f_dict)
        st = self._stats[mid]
        st["count"] += 1
        st["last_ingested"] = f_dict["submitted_at"]
        
        if f_dict["error"] is not None:
            st["error_sum"] += f_dict["error"]
            st["errors"].append(f_dict["error"])
            # Keep recent errors bounded
            if len(st["errors"]) > 1000:
                st["errors"] = st["errors"][-1000:]
                
        return f_dict["feedback_id"]

    async def ingest_risk_feedback(self, feedback: RiskFeedback) -> str:
        t0 = time.perf_counter()
        fid = await self._store_and_update_stats(feedback)
        log.debug(f"Ingested risk feedback {fid} in {time.perf_counter()-t0:.4f}s")
        return fid

    async def ingest_forecast_feedback(self, feedback: ForecastFeedback) -> str:
        t0 = time.perf_counter()
        fid = await self._store_and_update_stats(feedback)
        log.debug(f"Ingested forecast feedback {fid} in {time.perf_counter()-t0:.4f}s")
        return fid

    async def ingest_hazard_feedback(self, feedback: HazardFeedback) -> str:
        t0 = time.perf_counter()
        fid = await self._store_and_update_stats(feedback)
        return fid

    async def ingest_rca_feedback(self, feedback: RCAFeedback) -> str:
        t0 = time.perf_counter()
        fid = await self._store_and_update_stats(feedback)
        return fid

    async def ingest_twin_feedback(self, feedback: TwinFeedback) -> str:
        t0 = time.perf_counter()
        fid = await self._store_and_update_stats(feedback)
        return fid

    async def ingest_simulation_feedback(self, feedback: SimulationFeedback) -> str:
        t0 = time.perf_counter()
        fid = await self._store_and_update_stats(feedback)
        return fid

    async def ingest_batch(self, feedbacks: list[dict[str, Any]], feedback_type: str) -> dict[str, Any]:
        t0 = time.perf_counter()
        ingested = 0
        failed = 0
        feedback_ids = []
        
        for f_dict in feedbacks:
            try:
                # In real scenario we'd instantiate proper model based on type
                # For this implementation we'll manually dump to store
                mid = f_dict.get("model_id")
                if not mid:
                    failed += 1
                    continue
                    
                if "feedback_id" not in f_dict:
                    import uuid
                    f_dict["feedback_id"] = str(uuid.uuid4())
                if "submitted_at" not in f_dict:
                    f_dict["submitted_at"] = datetime.now(timezone.utc).isoformat()
                    
                if f_dict.get("error") is None:
                    f_dict["error"] = self._compute_error(f_dict)
                    
                if mid not in self._feedback_store:
                    self._feedback_store[mid] = []
                    self._stats[mid] = {"count": 0, "error_sum": 0.0, "last_ingested": None, "errors": []}
                    
                self._feedback_store[mid].append(f_dict)
                st = self._stats[mid]
                st["count"] += 1
                st["last_ingested"] = f_dict["submitted_at"]
                if f_dict["error"] is not None:
                    st["error_sum"] += f_dict["error"]
                    st["errors"].append(f_dict["error"])
                    if len(st["errors"]) > 1000:
                        st["errors"] = st["errors"][-1000:]
                        
                feedback_ids.append(f_dict["feedback_id"])
                ingested += 1
            except Exception as e:
                log.error(f"Failed to ingest feedback in batch: {e}")
                failed += 1
                
        latency = time.perf_counter() - t0
        log.info(f"Batch ingested {ingested} feedbacks, {failed} failed in {latency:.4f}s")
        
        return {
            "ingested": ingested,
            "failed": failed,
            "feedback_ids": feedback_ids
        }

    async def get_feedback_stats(self, model_id: str) -> dict[str, Any]:
        t0 = time.perf_counter()
        if model_id not in self._stats:
            return {
                "total": 0, "mean_error": 0.0, "std_error": 0.0,
                "recent_accuracy": 0.0, "trigger_threshold": self._trigger_threshold,
                "ready_for_update": False
            }
            
        st = self._stats[model_id]
        errs = st["errors"]
        
        mean_err = np.mean(errs) if errs else 0.0
        std_err = np.std(errs) if errs else 0.0
        
        # Simple accuracy proxy
        recent_acc = max(0.0, 1.0 - mean_err)
        
        ready = st["count"] >= self._trigger_threshold
        
        latency = time.perf_counter() - t0
        return {
            "total": st["count"],
            "mean_error": float(mean_err),
            "std_error": float(std_err),
            "recent_accuracy": float(recent_acc),
            "trigger_threshold": self._trigger_threshold,
            "ready_for_update": ready
        }

    async def get_recent_feedback(self, model_id: str, limit: int = 50) -> list[dict[str, Any]]:
        t0 = time.perf_counter()
        if model_id not in self._feedback_store:
            return []
            
        res = self._feedback_store[model_id][-limit:]
        log.debug(f"Retrieved {len(res)} feedbacks for {model_id} in {time.perf_counter()-t0:.4f}s")
        return res

    async def clear_processed_feedback(self, model_id: str, older_than_hours: int) -> int:
        t0 = time.perf_counter()
        if model_id not in self._feedback_store:
            return 0
            
        now_ts = datetime.now(timezone.utc).timestamp()
        cutoff = now_ts - (older_than_hours * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff, timezone.utc).isoformat()
        
        original_len = len(self._feedback_store[model_id])
        self._feedback_store[model_id] = [
            f for f in self._feedback_store[model_id] 
            if f.get("submitted_at", "") > cutoff_iso
        ]
        
        cleared = original_len - len(self._feedback_store[model_id])
        log.info(f"Cleared {cleared} feedbacks for {model_id} in {time.perf_counter()-t0:.4f}s")
        return cleared

_feedback_ingestion_instance = None

def get_feedback_ingestion_service() -> FeedbackIngestionService:
    global _feedback_ingestion_instance
    if _feedback_ingestion_instance is None:
        _feedback_ingestion_instance = FeedbackIngestionService()
    return _feedback_ingestion_instance
