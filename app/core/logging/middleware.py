"""
middleware.py — FastAPI request logging middleware.

Responsibility:
  - Generate request_id and correlation_id for every request
  - Populate the request context (ContextVars)
  - Log incoming requests and outgoing responses with latency
  - Propagate X-Request-ID and X-Correlation-ID response headers

Example log output (development):
    [2026-07-21 23:15:01]
    INFO
    abhedya.middleware
    → GET /api/v1/risk/current
    request_id=93ac-...  correlation_id=991e-...

    [2026-07-21 23:15:01]
    INFO
    abhedya.middleware
    ← 200 GET /api/v1/risk/current  123ms
    request_id=93ac-...  correlation_id=991e-...

Example JSON output (production):
    {"timestamp":"...","level":"INFO","service":"abhedya.middleware",
     "message":"← 200 GET /api/v1/risk/current  123ms",
     "request_id":"93ac-...","latency_ms":123,"status_code":200}
"""

import logging
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging.config import LoggingConfig
from app.core.logging.logger import get_logger
from app.core.logging.request_context import (
    clear_request_context,
    set_request_context,
)

log = get_logger("abhedya.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request and response with timing and context IDs.

    Automatically:
      - Reads X-Request-ID from the incoming request (or generates one)
      - Reads X-Correlation-ID from the incoming request (or generates one)
      - Populates the request context for downstream log records
      - Logs the request on arrival
      - Logs the response with status code and latency
      - Adds X-Request-ID and X-Correlation-ID to the response headers
      - Clears the context after the response is sent

    Health-check paths (configurable in LoggingConfig.SILENT_PATHS)
    are not logged to reduce noise.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # ── Extract or generate IDs ───────────────────────────────────────────
        request_id = (
            request.headers.get("X-Request-ID") or str(uuid.uuid4())
        )
        correlation_id = (
            request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        )

        # ── Populate async context ────────────────────────────────────────────
        set_request_context(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        path = request.url.path
        method = request.method
        silent = path in LoggingConfig.SILENT_PATHS

        # ── Log incoming request ──────────────────────────────────────────────
        if not silent:
            client_ip = self._get_client_ip(request)
            log.info(
                f"→ {method} {path}",
                extra={
                    "http_method": method,
                    "http_path": path,
                    "client_ip": client_ip,
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                },
            )

        # ── Process request ───────────────────────────────────────────────────
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            log.exception(
                f"✗ {method} {path}  {latency_ms}ms  [UNHANDLED EXCEPTION]",
                extra={
                    "http_method": method,
                    "http_path": path,
                    "latency_ms": latency_ms,
                },
            )
            clear_request_context()
            raise

        latency_ms = int((time.perf_counter() - start) * 1000)

        # ── Log response ──────────────────────────────────────────────────────
        if not silent:
            level = logging.WARNING if response.status_code >= 400 else logging.INFO
            log.log(
                level,
                f"← {response.status_code} {method} {path}  {latency_ms}ms",
                extra={
                    "http_method": method,
                    "http_path": path,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                },
            )

        # ── Propagate IDs in response headers ─────────────────────────────────
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id

        # ── Clean up context ──────────────────────────────────────────────────
        clear_request_context()
        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract the real client IP, respecting X-Forwarded-For."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"
