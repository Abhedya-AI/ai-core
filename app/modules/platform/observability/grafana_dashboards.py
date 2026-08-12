from __future__ import annotations

import uuid
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)


class GrafanaDashboardGenerator:
    def _create_prometheus_target(self, expr: str, legend: str) -> dict:
        return {
            "expr": expr,
            "legendFormat": legend,
            "refId": str(uuid.uuid4())[:8]
        }

    def _create_panel(self, panel_id: int, title: str, panel_type: str, targets: list[dict], gridPos: dict) -> dict:
        return {
            "id": panel_id,
            "title": title,
            "type": panel_type,
            "targets": targets,
            "gridPos": gridPos,
            "datasource": "Prometheus"
        }

    async def generate_ai_pipeline_dashboard(self) -> dict:
        panels = [
            self._create_panel(
                1, "HTTP Request Rate", "timeseries",
                [self._create_prometheus_target('rate(http_requests_total[5m])', '{{method}} {{endpoint}}')],
                {"h": 8, "w": 12, "x": 0, "y": 0}
            ),
            self._create_panel(
                2, "AI Pipeline Latency", "timeseries",
                [self._create_prometheus_target('histogram_quantile(0.95, rate(ai_pipeline_duration_seconds_bucket[5m]))', 'p95 {{module}}')],
                {"h": 8, "w": 12, "x": 12, "y": 0}
            ),
            self._create_panel(
                3, "Model Inference Count", "barchart",
                [self._create_prometheus_target('sum by (module) (rate(model_inference_total[5m]))', '{{module}}')],
                {"h": 8, "w": 8, "x": 0, "y": 8}
            ),
            self._create_panel(
                4, "Drift Alerts by Severity", "stat",
                [self._create_prometheus_target('sum by (severity) (drift_alerts_total)', '{{severity}}')],
                {"h": 8, "w": 8, "x": 8, "y": 8}
            ),
            self._create_panel(
                5, "Error Rate", "stat",
                [self._create_prometheus_target('sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))', 'Error Rate')],
                {"h": 8, "w": 8, "x": 16, "y": 8}
            )
        ]
        return {
            "title": "AI Pipeline Dashboard",
            "uid": str(uuid.uuid4()),
            "panels": panels,
            "templating": {"list": []},
            "time": {"from": "now-6h", "to": "now"},
            "refresh": "5s"
        }

    async def generate_model_performance_dashboard(self) -> dict:
        panels = [
            self._create_panel(1, "Model Accuracy Trend", "timeseries", [], {"h": 8, "w": 12, "x": 0, "y": 0}),
            self._create_panel(2, "F1 Score Trend", "timeseries", [], {"h": 8, "w": 12, "x": 12, "y": 0}),
            self._create_panel(3, "Inference Latency", "timeseries", [], {"h": 8, "w": 12, "x": 0, "y": 8}),
            self._create_panel(4, "Feature Drift Score", "timeseries", [], {"h": 8, "w": 12, "x": 12, "y": 8})
        ]
        return {
            "title": "Model Performance",
            "uid": str(uuid.uuid4()),
            "panels": panels,
            "time": {"from": "now-24h", "to": "now"},
            "refresh": "1m"
        }

    async def generate_system_health_dashboard(self) -> dict:
        panels = [
            self._create_panel(1, "Component Health Status", "stat", [], {"h": 6, "w": 24, "x": 0, "y": 0}),
            self._create_panel(2, "Kafka Consumer Lag", "timeseries", [], {"h": 8, "w": 12, "x": 0, "y": 6}),
            self._create_panel(3, "Redis Memory", "timeseries", [], {"h": 8, "w": 12, "x": 12, "y": 6}),
            self._create_panel(4, "PostgreSQL Connections", "timeseries", [], {"h": 8, "w": 12, "x": 0, "y": 14}),
            self._create_panel(5, "Active Tenants", "stat", [], {"h": 8, "w": 12, "x": 12, "y": 14})
        ]
        return {
            "title": "System Health",
            "uid": str(uuid.uuid4()),
            "panels": panels,
            "time": {"from": "now-1h", "to": "now"},
            "refresh": "10s"
        }

    async def generate_multi_plant_dashboard(self) -> dict:
        panels = [
            self._create_panel(1, "Per-Plant OEE", "barchart", [], {"h": 10, "w": 12, "x": 0, "y": 0}),
            self._create_panel(2, "Safety Index", "gauge", [], {"h": 10, "w": 12, "x": 12, "y": 0}),
            self._create_panel(3, "Active Incidents", "stat", [], {"h": 8, "w": 12, "x": 0, "y": 10}),
            self._create_panel(4, "Fleet Health Score", "stat", [], {"h": 8, "w": 12, "x": 12, "y": 10})
        ]
        return {
            "title": "Multi-Plant Operations",
            "uid": str(uuid.uuid4()),
            "panels": panels,
            "time": {"from": "now-7d", "to": "now"},
            "refresh": "5m"
        }
