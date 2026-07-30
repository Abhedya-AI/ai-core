"""
app/api/middleware/error_handler.py — Global Exception Handler Middleware.

Catches ALL unhandled exceptions in the request pipeline and converts them
to a structured ErrorResponse JSON body with the appropriate HTTP status code.

Priority chain:
  1. AbhedyaException subclasses → typed error code + status
  2. FastAPI / Pydantic RequestValidationError → 422 VALIDATION_ERROR
  3. Any other Exception → 500 INTERNAL_ERROR (no stack trace in production)
"""

from __future__ import annotations

import traceback

from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.api.exceptions import AbhedyaException
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("api.middleware.error_handler")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Converts unhandled exceptions to structured ErrorResponse JSON."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        try:
            return await call_next(request)

        except AbhedyaException as exc:
            # Typed domain / API exceptions — use their code + status
            request_id = getattr(request.state, "request_id", "unknown")
            log.warning(
                f"[{exc.code}] {exc.message} (path={request.url.path}, request_id={request_id})"
            )
            return JSONResponse(
                status_code=exc.status,
                content={
                    "success": False,
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "field": exc.field,
                        "details": exc.details if settings.app.debug else None,
                    },
                    "metadata": {
                        "trace_id": request_id,
                        "request_id": request_id,
                    },
                },
            )

        except RequestValidationError as exc:
            # Pydantic / FastAPI request body validation errors
            request_id = getattr(request.state, "request_id", "unknown")
            errors = [
                {
                    "field": " → ".join(str(l) for l in e["loc"]),
                    "message": e["msg"],
                    "type": e["type"],
                }
                for e in exc.errors()
            ]
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request validation failed.",
                        "details": errors,
                    },
                    "metadata": {
                        "trace_id": request_id,
                        "request_id": request_id,
                    },
                },
            )

        except Exception as exc:
            # Catch-all — never leak stack traces in production
            request_id = getattr(request.state, "request_id", "unknown")
            log.error(
                f"Unhandled exception on {request.method} {request.url.path}: {exc}\n"
                + (traceback.format_exc() if settings.app.debug else "")
            )
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred. Please try again later.",
                        "details": str(exc) if settings.app.debug else None,
                    },
                    "metadata": {
                        "trace_id": request_id,
                        "request_id": request_id,
                    },
                },
            )
