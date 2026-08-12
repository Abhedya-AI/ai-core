from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

from app.core.logging import get_logger
log = get_logger(__name__)


class AIPipelineMetricsCollector:
    def __init__(self):
        self._module_metrics: dict[str, list[dict]] = {}

    def _add_metric(self, module: str, data: dict) -> None:
        if module not in self._module_metrics:
            self._module_metrics[module] = []
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        data["module"] = module
        data["timestamp_pc"] = time.perf_counter()
        self._module_metrics[module].append(data)

    async def record_risk_prediction(self, entity_id: str, latency_ms: float, risk_score: float, confidence: float) -> None:
        self._add_metric("risk_prediction", {
            "entity_id": entity_id,
            "latency_ms": latency_ms,
            "risk_score": risk_score,
            "confidence": confidence
        })

    async def record_forecast(self, entity_id: str, forecast_type: str, horizon: int, latency_ms: float, confidence: float) -> None:
        self._add_metric("forecast", {
            "entity_id": entity_id,
            "forecast_type": forecast_type,
            "horizon": horizon,
            "latency_ms": latency_ms,
            "confidence": confidence
        })

    async def record_hazard_detection(self, zone_id: str, hazard_type: str, propagation_steps: int, latency_ms: float, severity_score: float) -> None:
        self._add_metric("hazard_detection", {
            "zone_id": zone_id,
            "hazard_type": hazard_type,
            "propagation_steps": propagation_steps,
            "latency_ms": latency_ms,
            "severity_score": severity_score
        })

    async def record_simulation(self, simulation_type: str, latency_ms: float, steps: int, outcome: str) -> None:
        self._add_metric("simulation", {
            "simulation_type": simulation_type,
            "latency_ms": latency_ms,
            "steps": steps,
            "outcome": outcome
        })

    async def record_twin_sync(self, sync_source: str, entity_count: int, latency_ms: float, success: bool) -> None:
        self._add_metric("twin_sync", {
            "sync_source": sync_source,
            "entity_count": entity_count,
            "latency_ms": latency_ms,
            "success": success
        })

    async def record_rca(self, incident_id: str, latency_ms: float, cause_count: int, confidence: float) -> None:
        self._add_metric("rca", {
            "incident_id": incident_id,
            "latency_ms": latency_ms,
            "cause_count": cause_count,
            "confidence": confidence
        })

    async def get_module_stats(self, module: str, window_minutes: int = 60) -> dict:
        records = self._module_metrics.get(module, [])
        cutoff = time.perf_counter() - (window_minutes * 60)
        recent = [r for r in records if r.get("timestamp_pc", 0) >= cutoff]
        
        count = len(recent)
        if count == 0 or np is None:
            return {
                "count": count,
                "mean_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "error_rate": 0.0,
                "mean_confidence": 0.0
            }
        
        latencies = [r.get("latency_ms", 0.0) for r in recent]
        confidences = [r.get("confidence", 0.0) for r in recent if "confidence" in r]
        errors = [r for r in recent if r.get("success") is False or r.get("outcome") == "failed"]
        
        return {
            "count": count,
            "mean_latency_ms": float(np.mean(latencies)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
            "p99_latency_ms": float(np.percentile(latencies, 99)),
            "error_rate": len(errors) / count if count else 0.0,
            "mean_confidence": float(np.mean(confidences)) if confidences else 0.0
        }

    async def get_system_throughput(self, window_minutes: int = 5) -> dict:
        cutoff = time.perf_counter() - (window_minutes * 60)
        total_requests = 0
        by_module = {}
        for module, records in self._module_metrics.items():
            recent_count = sum(1 for r in records if r.get("timestamp_pc", 0) >= cutoff)
            by_module[module] = recent_count
            total_requests += recent_count
            
        return {
            "total_requests": total_requests,
            "requests_per_second": total_requests / (window_minutes * 60),
            "by_module": by_module
        }

    async def get_performance_summary(self) -> dict:
        summary = {}
        for module in self._module_metrics.keys():
            summary[module] = await self.get_module_stats(module)
        return summary
