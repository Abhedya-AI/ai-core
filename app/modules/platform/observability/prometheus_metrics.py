from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class NoOpMetric:
    def inc(self, amount: float = 1) -> NoOpMetric:
        return self

    def observe(self, amount: float) -> NoOpMetric:
        return self

    def set(self, amount: float) -> NoOpMetric:
        return self

    def labels(self, **kwargs) -> NoOpMetric:
        return self


class PrometheusMetricsCollector:
    def __init__(self):
        self._metrics_data: dict[str, Any] = {}
        if PROMETHEUS_AVAILABLE:
            self.http_requests_total = Counter(
                "http_requests_total",
                "Total HTTP requests",
                labelnames=["method", "endpoint", "status_code"]
            )
            self.http_request_duration_seconds = Histogram(
                "http_request_duration_seconds",
                "HTTP request duration in seconds",
                bins=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
            )
            self.ai_pipeline_duration_seconds = Histogram(
                "ai_pipeline_duration_seconds",
                "AI pipeline duration in seconds",
                labelnames=["module", "operation"]
            )
            self.model_inference_total = Counter(
                "model_inference_total",
                "Total model inferences",
                labelnames=["model_id", "module", "status"]
            )
            self.drift_alerts_total = Counter(
                "drift_alerts_total",
                "Total drift alerts",
                labelnames=["model_id", "drift_type", "severity"]
            )
            self.simulation_runs_total = Counter(
                "simulation_runs_total",
                "Total simulation runs",
                labelnames=["simulation_type", "status"]
            )
            self.twin_sync_events_total = Counter(
                "twin_sync_events_total",
                "Total twin sync events",
                labelnames=["sync_source", "status"]
            )
            self.active_tenants = Gauge("active_tenants", "Active tenants")
            self.active_model_versions = Gauge("active_model_versions", "Active model versions")
            self.kafka_events_published_total = Counter(
                "kafka_events_published_total",
                "Total Kafka events published",
                labelnames=["topic", "status"]
            )
            self.redis_cache_hits_total = Counter(
                "redis_cache_hits_total",
                "Redis cache hits",
                labelnames=["operation"]
            )
            self.redis_cache_misses_total = Counter(
                "redis_cache_misses_total",
                "Redis cache misses",
                labelnames=["operation"]
            )
            self.feature_store_operations_total = Counter(
                "feature_store_operations_total",
                "Feature store operations",
                labelnames=["operation", "store_type"]
            )
        else:
            self.http_requests_total = NoOpMetric()
            self.http_request_duration_seconds = NoOpMetric()
            self.ai_pipeline_duration_seconds = NoOpMetric()
            self.model_inference_total = NoOpMetric()
            self.drift_alerts_total = NoOpMetric()
            self.simulation_runs_total = NoOpMetric()
            self.twin_sync_events_total = NoOpMetric()
            self.active_tenants = NoOpMetric()
            self.active_model_versions = NoOpMetric()
            self.kafka_events_published_total = NoOpMetric()
            self.redis_cache_hits_total = NoOpMetric()
            self.redis_cache_misses_total = NoOpMetric()
            self.feature_store_operations_total = NoOpMetric()

    def record_http_request(self, method: str, endpoint: str, status_code: int, duration_seconds: float) -> None:
        self.http_requests_total.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
        self.http_request_duration_seconds.observe(duration_seconds)
        self._metrics_data["http_requests_total"] = self._metrics_data.get("http_requests_total", 0) + 1

    def record_ai_pipeline(self, module: str, operation: str, duration_seconds: float) -> None:
        self.ai_pipeline_duration_seconds.labels(module=module, operation=operation).observe(duration_seconds)

    def record_model_inference(self, model_id: str, module: str, status: str) -> None:
        self.model_inference_total.labels(model_id=model_id, module=module, status=status).inc()

    def record_drift_alert(self, model_id: str, drift_type: str, severity: str) -> None:
        self.drift_alerts_total.labels(model_id=model_id, drift_type=drift_type, severity=severity).inc()

    def record_simulation_run(self, simulation_type: str, status: str) -> None:
        self.simulation_runs_total.labels(simulation_type=simulation_type, status=status).inc()

    def set_active_tenants(self, count: int) -> None:
        self.active_tenants.set(count)
        self._metrics_data["active_tenants"] = count

    def set_active_model_versions(self, count: int) -> None:
        self.active_model_versions.set(count)
        self._metrics_data["active_model_versions"] = count

    def get_metrics_summary(self) -> dict:
        return self._metrics_data.copy()
