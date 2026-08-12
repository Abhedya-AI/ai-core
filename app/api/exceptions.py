"""
app/api/exceptions.py — ABHEDYA API exception hierarchy.

All application-layer exceptions map to a structured ErrorResponse
via the ExceptionHandlerMiddleware. Never raise raw HTTPException
inside business logic — raise a typed AbhedyaException and let
the middleware convert it.
"""

from __future__ import annotations

from http import HTTPStatus


class AbhedyaException(Exception):
    """
    Base ABHEDYA API exception.

    Attributes:
        code:       Machine-readable error code (ALL_CAPS_SNAKE).
        message:    Human-readable error description.
        status:     HTTP status code to return to the client.
        details:    Optional structured debug payload (never included in production).
        field:      Offending request field (validation errors only).
    """

    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."
    status: int = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: dict | None = None,
        field: str | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.code = code or self.__class__.code
        self.details = details
        self.field = field
        super().__init__(self.message)


# ── Authentication ─────────────────────────────────────────────────────────────

class AuthenticationError(AbhedyaException):
    """Token absent, invalid, or expired."""
    code = "AUTH_REQUIRED"
    message = "Authentication is required to access this resource."
    status = HTTPStatus.UNAUTHORIZED


class TokenExpiredError(AuthenticationError):
    """JWT access token has expired."""
    code = "AUTH_TOKEN_EXPIRED"
    message = "Your access token has expired. Please refresh."


class TokenInvalidError(AuthenticationError):
    """JWT signature invalid or tampered."""
    code = "AUTH_TOKEN_INVALID"
    message = "The provided token is invalid."


class ApiKeyInvalidError(AuthenticationError):
    """API key not found or revoked."""
    code = "AUTH_API_KEY_INVALID"
    message = "The provided API key is invalid or has been revoked."


# ── Authorization ──────────────────────────────────────────────────────────────

class PermissionDeniedError(AbhedyaException):
    """Caller lacks required permission."""
    code = "AUTHZ_PERMISSION_DENIED"
    message = "You do not have permission to perform this action."
    status = HTTPStatus.FORBIDDEN


class ResourceOwnershipError(PermissionDeniedError):
    """Caller does not own the requested resource."""
    code = "AUTHZ_NOT_RESOURCE_OWNER"
    message = "You do not have access to this resource."


# ── Resource ───────────────────────────────────────────────────────────────────

class NotFoundError(AbhedyaException):
    """Requested resource not found."""
    code = "RESOURCE_NOT_FOUND"
    message = "The requested resource was not found."
    status = HTTPStatus.NOT_FOUND


class ConflictError(AbhedyaException):
    """Duplicate resource or concurrent modification conflict."""
    code = "RESOURCE_CONFLICT"
    message = "A resource conflict prevented the operation."
    status = HTTPStatus.CONFLICT


# ── Validation ─────────────────────────────────────────────────────────────────

class ValidationError(AbhedyaException):
    """Input schema validation failure."""
    code = "VALIDATION_ERROR"
    message = "Request validation failed."
    status = HTTPStatus.UNPROCESSABLE_ENTITY


# ── Rate Limiting ──────────────────────────────────────────────────────────────

class RateLimitExceededError(AbhedyaException):
    """Request rate limit exceeded for this identity tier."""
    code = "RATE_LIMIT_EXCEEDED"
    message = "Rate limit exceeded. Please retry after the indicated wait period."
    status = HTTPStatus.TOO_MANY_REQUESTS


# ── Service ────────────────────────────────────────────────────────────────────

class ServiceUnavailableError(AbhedyaException):
    """Downstream dependency (DB, graph, LLM) is unreachable."""
    code = "SERVICE_UNAVAILABLE"
    message = "A required service is currently unavailable. Please try again later."
    status = HTTPStatus.SERVICE_UNAVAILABLE


class AgentExecutionError(AbhedyaException):
    """Agent failed to complete execution."""
    code = "AGENT_EXECUTION_FAILED"
    message = "An AI agent failed to complete the requested task."
    status = HTTPStatus.INTERNAL_SERVER_ERROR
