"""
app/api/middleware/request_id.py — Request ID / Trace ID Middleware.

Generates a unique UUID trace ID per request and attaches it to:
  - request.state.request_id  (readable by route handlers)
  - X-Request-ID response header  (readable by clients / load balancers)
  - X-Trace-ID response header    (alias for APM correlation)

If the client supplies X-Request-ID, that value is preserved and echoed back
to support end-to-end correlation with upstream systems.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates or propagates a unique request / trace ID
    for every HTTP request.
    """

    REQUEST_ID_HEADER = "X-Request-ID"
    TRACE_ID_HEADER = "X-Trace-ID"

    def __init__(self, app: ASGIApp, *, header_name: str = REQUEST_ID_HEADER) -> None:
        super().__init__(app)
        self._header_name = header_name

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        # Prefer upstream ID, otherwise generate new UUID
        request_id = request.headers.get(self._header_name) or str(uuid.uuid4())

        # Attach to request state so handlers can read it
        request.state.request_id = request_id

        response: Response = await call_next(request)

        # Echo back on response so clients can correlate logs
        response.headers[self.REQUEST_ID_HEADER] = request_id
        response.headers[self.TRACE_ID_HEADER] = request_id
        return response
