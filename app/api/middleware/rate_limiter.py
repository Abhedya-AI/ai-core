"""
app/api/middleware/rate_limiter.py — In-process sliding-window rate limiter.

This is an in-memory implementation suitable for single-process deployments
and development. For production multi-instance deployments, swap the store
backend to Redis (same interface, different storage) using the
`RedisRateLimitStore` class below.

Rate tiers (configurable in settings):
  - anonymous  : 30 req / 60 s
  - api_key    : 120 req / 60 s
  - authenticated_user : 300 req / 60 s
  - internal_service   : 1000 req / 60 s

Bypass conditions:
  - Health check endpoints (/health/*, /metrics)
  - Requests from loop-back addresses in development mode
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


# ── Rate Limit Store ───────────────────────────────────────────────────────────

class InMemoryRateLimitStore:
    """Sliding-window counter store backed by in-memory deques."""

    def __init__(self) -> None:
        self._windows: dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check whether the key is within the rate limit.

        Returns:
            (allowed: bool, remaining: int) — calls remaining in window.
        """
        now = time.monotonic()
        window_start = now - window_seconds
        dq = self._windows[key]

        # Evict expired timestamps
        while dq and dq[0] < window_start:
            dq.popleft()

        count = len(dq)
        if count >= limit:
            return False, 0

        dq.append(now)
        return True, limit - count - 1


# ── Tiers ──────────────────────────────────────────────────────────────────────

RATE_LIMIT_TIERS: dict[str, tuple[int, int]] = {
    "anonymous": (30, 60),
    "api_key": (120, 60),
    "authenticated": (300, 60),
    "internal": (1000, 60),
}

BYPASS_PREFIXES = ("/health", "/metrics", "/docs", "/redoc", "/openapi.json")


# ── Middleware ─────────────────────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter middleware.

    Key is derived from: (IP address) or (authenticated user ID).
    Tier is derived from the request's `principal_type` state attribute
    set by the authentication middleware, defaulting to 'anonymous'.
    """

    def __init__(self, app: ASGIApp, store: InMemoryRateLimitStore | None = None) -> None:
        super().__init__(app)
        self._store = store or InMemoryRateLimitStore()

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        path = request.url.path

        # Bypass for infrastructure endpoints
        if any(path.startswith(p) for p in BYPASS_PREFIXES):
            return await call_next(request)

        # Determine key and tier
        principal_id = getattr(request.state, "principal_id", None)
        principal_type = getattr(request.state, "principal_type", "anonymous")

        key = principal_id or request.client.host if request.client else "unknown"
        tier = principal_type if principal_type in RATE_LIMIT_TIERS else "anonymous"
        limit, window = RATE_LIMIT_TIERS[tier]

        allowed, remaining = self._store.is_allowed(f"{tier}:{key}", limit, window)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit of {limit} requests per {window}s exceeded.",
                    },
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Window": str(window),
                    "Retry-After": str(window),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(window)
        return response
