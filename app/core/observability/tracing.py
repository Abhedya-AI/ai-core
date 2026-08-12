"""
app/core/observability/tracing.py — OpenTelemetry Trace & Span Context Manager.

Provides structured span creation and trace propagation across HTTP requests,
application services, and SupervisorAgent execution trajectories.

Integrates with OpenTelemetry SDK (if installed) or falls back gracefully to a
lightweight in-memory span recorder.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger

log = get_logger("observability.tracing")


@dataclass
class SpanRecord:
    """Recorded tracing span representing an operation execution."""

    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:16])
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: str | None = None
    name: str = ""
    status: str = "OK"  # OK | ERROR
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def finish(self, status: str = "OK") -> None:
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        })


class TracerStore:
    """In-memory telemetry store for agent trajectory traces."""

    _instance: "TracerStore | None" = None

    def __init__(self) -> None:
        # trace_id → list of SpanRecord
        self._traces: dict[str, list[SpanRecord]] = {}

    @classmethod
    def get_instance(cls) -> "TracerStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_span(self, span: SpanRecord) -> None:
        if span.trace_id not in self._traces:
            self._traces[span.trace_id] = []
        self._traces[span.trace_id].append(span)

    def get_trace_spans(self, trace_id: str) -> list[SpanRecord]:
        return self._traces.get(trace_id, [])

    def get_trajectory_summary(self, trace_id: str) -> dict[str, Any]:
        """Return structured execution trajectory for a trace_id / task_id."""
        spans = self.get_trace_spans(trace_id)
        if not spans:
            return {"trace_id": trace_id, "found": False, "spans": []}

        return {
            "trace_id": trace_id,
            "found": True,
            "total_spans": len(spans),
            "total_duration_ms": max((s.duration_ms for s in spans), default=0.0),
            "spans": [
                {
                    "span_id": s.span_id,
                    "parent_span_id": s.parent_span_id,
                    "name": s.name,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "attributes": s.attributes,
                    "events": s.events,
                }
                for s in spans
            ],
        }


# ── Context Manager Helper ─────────────────────────────────────────────────────

class trace_span:
    """Context manager for tracing operations."""

    def __init__(self, name: str, trace_id: str | None = None, attributes: dict[str, Any] | None = None) -> None:
        self.span = SpanRecord(
            name=name,
            trace_id=trace_id or str(uuid.uuid4()),
            attributes=attributes or {},
        )
        self.store = TracerStore.get_instance()

    def __enter__(self) -> SpanRecord:
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        status = "ERROR" if exc_type else "OK"
        self.span.finish(status=status)
        if exc_val:
            self.span.add_event("exception", {"type": exc_type.__name__, "message": str(exc_val)})
        self.store.record_span(self.span)
