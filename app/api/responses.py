"""
app/api/responses.py — Standardized API response envelopes.

Every endpoint returns one of:
  - StandardResponse[T]   — single resource / action result
  - PaginatedResponse[T]  — list with cursor-based pagination
  - ErrorResponse         — machine-readable error with trace context

The frontend / SDK MUST NOT parse HTTP status codes for business logic.
Read `success`, `data`, and `error.code` instead.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Metadata ───────────────────────────────────────────────────────────────────

class ResponseMetadata(BaseModel):
    """Timing and tracing metadata attached to every response."""

    trace_id: str
    request_id: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    execution_time_ms: int = 0
    version: str = "1.0.0"


# ── Error ──────────────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """Structured error information returned on failure."""

    code: str = Field(..., description="Machine-readable error code e.g. AUTH_TOKEN_EXPIRED")
    message: str = Field(..., description="Human-readable error description")
    field: str | None = Field(default=None, description="Offending field for validation errors")
    details: dict[str, Any] | None = Field(default=None)


class ErrorResponse(BaseModel):
    """Envelope for all error responses — always success=False."""

    success: bool = False
    error: ErrorDetail
    metadata: ResponseMetadata


# ── Success ────────────────────────────────────────────────────────────────────

class StandardResponse(BaseModel, Generic[T]):
    """
    Envelope for all successful single-resource responses.

    Example::

        return StandardResponse(
            success=True,
            data=IncidentDTO(...),
            metadata=ResponseMetadata(trace_id=..., request_id=...),
        )
    """

    success: bool = True
    data: T
    metadata: ResponseMetadata


# ── Pagination ─────────────────────────────────────────────────────────────────

class PaginationMeta(BaseModel):
    """Cursor-based pagination context."""

    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
    next_cursor: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Envelope for list-of-resources responses."""

    success: bool = True
    data: list[T]
    pagination: PaginationMeta
    metadata: ResponseMetadata


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_response(
    data: T,
    trace_id: str = "trace-default",
    request_id: str = "req-default",
    execution_time_ms: int = 0,
    meta: Any = None,
) -> StandardResponse[T]:
    """Convenience factory for StandardResponse."""
    t_id = getattr(meta, 'trace_id', trace_id) if meta else trace_id
    r_id = getattr(meta, 'request_id', request_id) if meta else request_id
    return StandardResponse(
        data=data,
        metadata=ResponseMetadata(
            trace_id=str(t_id),
            request_id=str(r_id),
            execution_time_ms=execution_time_ms,
        ),
    )


def make_error(
    code: str,
    message: str,
    trace_id: str,
    request_id: str,
    field: str | None = None,
    details: dict[str, Any] | None = None,
) -> ErrorResponse:
    """Convenience factory for ErrorResponse."""
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, field=field, details=details),
        metadata=ResponseMetadata(trace_id=trace_id, request_id=request_id),
    )
