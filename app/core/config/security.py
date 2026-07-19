"""
security.py — Security and authentication settings.

Responsibility: JWT configuration, secret key, CORS policy, API key auth.
No cryptographic operations here — just configuration values.
"""

from pydantic import Field, field_validator

from app.core.config._base import _BaseConfig

_UNSAFE_DEFAULT_KEY = "change-me-in-production"


class SecuritySettings(_BaseConfig):
    """JWT, CORS, and API authentication settings."""

    # ── JWT ───────────────────────────────────────────────────────────────────
    secret_key: str = Field(
        default=_UNSAFE_DEFAULT_KEY,
        alias="SECRET_KEY",
        description="Secret key used to sign JWT tokens. MUST be changed in production.",
    )
    algorithm: str = Field(
        default="HS256",
        alias="ALGORITHM",
        description="JWT signing algorithm.",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="JWT access token lifetime in minutes.",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
        description="JWT refresh token lifetime in days.",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="ALLOWED_ORIGINS",
        description="List of allowed CORS origins.",
    )
    allowed_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        alias="ALLOWED_METHODS",
        description="List of allowed CORS HTTP methods.",
    )
    allowed_headers: list[str] = Field(
        default=["*"],
        alias="ALLOWED_HEADERS",
        description="List of allowed CORS headers.",
    )
    allow_credentials: bool = Field(
        default=True,
        alias="ALLOW_CREDENTIALS",
        description="Whether to allow cookies/credentials in CORS requests.",
    )

    # ── API Key Auth (optional) ───────────────────────────────────────────────
    api_key_enabled: bool = Field(
        default=False,
        alias="API_KEY_ENABLED",
        description="Require X-API-Key header on all requests.",
    )
    api_key: str | None = Field(
        default=None,
        alias="API_KEY",
        description="The API key value when api_key_enabled=True.",
    )

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    rate_limit_enabled: bool = Field(
        default=False,
        alias="RATE_LIMIT_ENABLED",
        description="Enable request rate limiting.",
    )
    rate_limit_per_minute: int = Field(
        default=60,
        alias="RATE_LIMIT_PER_MINUTE",
        description="Maximum requests per minute per client IP.",
    )

    # ── Validation ────────────────────────────────────────────────────────────

    @field_validator("secret_key")
    @classmethod
    def _secret_key_must_be_set_in_production(cls, v: str) -> str:
        """
        The validator runs on every instantiation.
        In production, an unsafe default key is a critical misconfiguration.
        """
        import os
        if os.getenv("APP_ENV") == "production" and v == _UNSAFE_DEFAULT_KEY:
            raise ValueError(
                "SECRET_KEY must be changed in production. "
                "Set a strong random value in .env.production."
            )
        return v

    @property
    def is_key_unsafe(self) -> bool:
        """True if the secret key is still the default placeholder."""
        return self.secret_key == _UNSAFE_DEFAULT_KEY
