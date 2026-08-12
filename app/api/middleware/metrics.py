"""
app/api/middleware/metrics.py — Request Metrics Middleware.

Captures per-request telemetry:
  - Method + path + status code
  - Request latency (ms)
  - Request size (bytes)

Metrics are stored in a module-level `RequestMetricsStore` and exposed
at GET /metrics in Prometheus text format via the health router.

For production, swap the store to a Prometheus client library or
push to Datadog / CloudWatch.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field


# ── In-memory Store ────────────────────────────────────────────────────────────

@dataclass
class EndpointMetrics:
    """Accumulated metrics for a single endpoint."""

    request_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0

    def record(self, latency_ms: float, is_error: bool) -> None:
        self.request_count += 1
        self.total_latency_ms += latency_ms
        self.min_latency_ms = min(self.min_latency_ms, latency_ms)
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)
        if is_error:
            self.error_count += 1

    @property
    def avg_latency_ms(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.total_latency_ms / self.request_count


class RequestMetricsStore:
    """Singleton in-memory metrics store."""

    _instance: "RequestMetricsStore | None" = None

    def __init__(self) -> None:
        # key: "METHOD /path" → EndpointMetrics
        self._endpoints: dict[str, EndpointMetrics] = defaultdict(EndpointMetrics)
        self._total_requests: int = 0
        self._total_errors: int = 0

    @classmethod
    def get_instance(cls) -> "RequestMetricsStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record(self, method: str, path: str, status_code: int, latency_ms: float) -> None:
        key = f"{method} {path}"
        is_error = status_code >= 500
        self._endpoints[key].record(latency_ms, is_error)
        self._total_requests += 1
        if is_error:
            self._total_errors += 1

    def to_prometheus_text(self) -> str:
        """Export as Prometheus text format."""
        lines = [
            "# HELP abhedya_requests_total Total HTTP requests",
            "# TYPE abhedya_requests_total counter",
            f"abhedya_requests_total {self._total_requests}",
            "# HELP abhedya_errors_total Total HTTP 5xx errors",
            "# TYPE abhedya_errors_total counter",
            f"abhedya_errors_total {self._total_errors}",
            "# HELP abhedya_request_latency_ms Average request latency per endpoint",
            "# TYPE abhedya_request_latency_ms gauge",
        ]
        for key, metrics in self._endpoints.items():
            method, path = key.split(" ", 1)
            label = f'method="{method}",path="{path}"'
            lines.append(f"abhedya_request_latency_ms{{{label}}} {metrics.avg_latency_ms:.2f}")
        return "\n".join(lines)

    def summary(self) -> dict:
        """Return summary dict for /health/metrics JSON."""
        return {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "endpoints": {
                k: {
                    "requests": v.request_count,
                    "errors": v.error_count,
                    "avg_latency_ms": round(v.avg_latency_ms, 2),
                    "min_latency_ms": round(v.min_latency_ms, 2) if v.min_latency_ms != float("inf") else 0,
                    "max_latency_ms": round(v.max_latency_ms, 2),
                }
                for k, v in self._endpoints.items()
            },
        }


# ── Middleware ─────────────────────────────────────────────────────────────────

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class MetricsMiddleware(BaseHTTPMiddleware):
    """Records per-request latency and status codes into RequestMetricsStore."""

    def __init__(self, app: ASGIApp, store: RequestMetricsStore | None = None) -> None:
        super().__init__(app)
        self._store = store or RequestMetricsStore.get_instance()

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000

        # Normalize path (strip query string, truncate dynamic segments)
        path = request.url.path
        self._store.record(request.method, path, response.status_code, latency_ms)

        response.headers["X-Response-Time-Ms"] = str(int(latency_ms))
        return response
