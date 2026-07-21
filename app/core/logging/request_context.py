"""
request_context.py — Per-request context via Python ContextVars.

Responsibility: store and retrieve per-request metadata using contextvars
so it is automatically propagated through async call stacks.

Stored context:
  request_id      — unique ID for this HTTP request
  correlation_id  — caller-supplied ID for distributed tracing
  user_id         — authenticated user (if available)
  service_name    — name of the originating service
  environment     — runtime environment (development | production)

Usage:
    # In middleware:
    set_request_context(request_id="abc", correlation_id="xyz")

    # In any logger filter:
    ctx = get_request_context()
    record.request_id = ctx["request_id"]
"""

from contextvars import ContextVar, Token
from typing import Optional
import uuid

from app.core.config import settings

# ── Context variables ─────────────────────────────────────────────────────────
_request_id: ContextVar[str] = ContextVar("request_id", default="")
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
_service_name: ContextVar[str] = ContextVar("service_name", default="abhedya")
_environment: ContextVar[str] = ContextVar(
    "environment", default=settings.app.environment
)


def set_request_context(
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
    user_id: str | None = None,
    service_name: str | None = None,
    environment: str | None = None,
) -> None:
    """
    Populate the request context for the current async task.

    Should be called at the start of each request in middleware.
    Values persist for the lifetime of the current async context.
    """
    _request_id.set(request_id or str(uuid.uuid4()))
    _correlation_id.set(correlation_id or str(uuid.uuid4()))
    if user_id is not None:
        _user_id.set(user_id)
    if service_name is not None:
        _service_name.set(service_name)
    if environment is not None:
        _environment.set(environment)


def get_request_context() -> dict[str, str | None]:
    """Return all context values as a plain dict."""
    return {
        "request_id": _request_id.get() or None,
        "correlation_id": _correlation_id.get() or None,
        "user_id": _user_id.get(),
        "service_name": _service_name.get(),
        "environment": _environment.get(),
    }


def clear_request_context() -> None:
    """
    Reset context to defaults.

    Call at the end of each request to prevent context leaks
    between requests reusing the same thread/task.
    """
    _request_id.set("")
    _correlation_id.set("")
    _user_id.set(None)
    _service_name.set("abhedya")
    _environment.set(settings.app.environment)
