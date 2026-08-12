from __future__ import annotations

import logging
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class NoOpInstrument:
    def add(self, value: float, attributes: dict | None = None) -> None:
        pass

    def record(self, value: float, attributes: dict | None = None) -> None:
        pass


class NoOpMeter:
    def create_counter(self, name: str, **kwargs) -> NoOpInstrument:
        return NoOpInstrument()

    def create_histogram(self, name: str, **kwargs) -> NoOpInstrument:
        return NoOpInstrument()


class NoOpTracer:
    class _SpanContextManager:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    def start_as_current_span(self, name: str, **kwargs) -> _SpanContextManager:
        return self._SpanContextManager()


class OpenTelemetrySetup:
    def __init__(self, service_name: str = "abhedya", otlp_endpoint: str = "http://localhost:4317"):
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint

    def setup(self) -> None:
        if OTEL_AVAILABLE:
            provider = TracerProvider()
            exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            log.info("OpenTelemetry setup complete")
        else:
            log.warning("OpenTelemetry not available. Using NoOp implementation.")

    def get_tracer(self, name: str) -> Any:
        if OTEL_AVAILABLE:
            return trace.get_tracer(name)
        return NoOpTracer()

    def get_meter(self, name: str) -> Any:
        if OTEL_AVAILABLE:
            return metrics.get_meter(name)
        return NoOpMeter()

    def create_span_context(self, trace_id: str, span_id: str) -> dict:
        return {"trace_id": trace_id, "span_id": span_id, "flags": 1}

    def extract_context_from_headers(self, headers: dict) -> dict:
        traceparent = headers.get("traceparent", "")
        if traceparent.startswith("00-") and len(traceparent.split("-")) == 4:
            parts = traceparent.split("-")
            return {"trace_id": parts[1], "span_id": parts[2]}
        return {}
