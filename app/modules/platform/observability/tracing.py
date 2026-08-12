from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.platform.observability.otel_setup import OpenTelemetrySetup

log = get_logger(__name__)


class DistributedTracer:
    def __init__(self, setup: OpenTelemetrySetup | None = None):
        self.setup = setup or OpenTelemetrySetup()
        self.tracer = self.setup.get_tracer("platform.distributed_tracer")

    async def trace_request(self, request_id: str, method: str, path: str, tenant_id: str) -> dict:
        trace_id = uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        started_at = datetime.now(timezone.utc).isoformat()
        return {
            "trace_id": trace_id,
            "span_id": span_id,
            "request_id": request_id,
            "tenant_id": tenant_id,
            "method": method,
            "path": path,
            "started_at": started_at,
            "start_time_pc": time.perf_counter()
        }

    async def trace_ai_pipeline(self, module: str, operation: str, entity_id: str, tenant_id: str) -> dict:
        trace_id = uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        started_at = datetime.now(timezone.utc).isoformat()
        return {
            "trace_id": trace_id,
            "span_id": span_id,
            "module": module,
            "operation": operation,
            "entity_id": entity_id,
            "tenant_id": tenant_id,
            "started_at": started_at,
            "start_time_pc": time.perf_counter()
        }

    async def finish_span(self, span_context: dict, status: str = "OK", error: str | None = None) -> dict:
        start_time_pc = span_context.get("start_time_pc", time.perf_counter())
        duration_ms = (time.perf_counter() - start_time_pc) * 1000
        result = dict(span_context)
        result.update({
            "duration_ms": duration_ms,
            "status": status
        })
        if error:
            result["error"] = error
        result.pop("start_time_pc", None)
        return result

    async def propagate_context(self, headers: dict) -> dict:
        return self.setup.extract_context_from_headers(headers)

    async def inject_context(self, context: dict, headers: dict) -> dict:
        trace_id = context.get("trace_id", "")
        span_id = context.get("span_id", "")
        if trace_id and span_id:
            headers["traceparent"] = f"00-{trace_id}-{span_id}-01"
        return headers

    async def create_child_span(self, parent_context: dict, name: str) -> dict:
        child_context = dict(parent_context)
        child_context["span_id"] = uuid.uuid4().hex[:16]
        child_context["parent_span_id"] = parent_context.get("span_id", "")
        child_context["name"] = name
        child_context["started_at"] = datetime.now(timezone.utc).isoformat()
        child_context["start_time_pc"] = time.perf_counter()
        return child_context
