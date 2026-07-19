"""
app.py — Application identity settings.

Responsibility: application name, version, environment, debug flag, API prefix.
Nothing else.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config._base import _BaseConfig


class AppSettings(_BaseConfig):
    """Application identity and runtime mode."""

    name: str = Field(
        default="ABHEDYA",
        alias="APP_NAME",
        description="Human-readable application name.",
    )
    version: str = Field(
        default="1.0.0",
        alias="APP_VERSION",
        description="Semantic version of the application.",
    )
    env: str = Field(
        default="development",
        alias="APP_ENV",
        description="Runtime environment: development | testing | production.",
    )
    debug: bool = Field(
        default=True,
        alias="APP_DEBUG",
        description="Enable debug mode. Must be False in production.",
    )
    api_prefix: str = Field(
        default="/api/v1",
        alias="API_PREFIX",
        description="Global API route prefix.",
    )
    host: str = Field(
        default="0.0.0.0",
        alias="HOST",
        description="Uvicorn bind host.",
    )
    port: int = Field(
        default=8000,
        alias="PORT",
        description="Uvicorn bind port.",
    )

    # ── Derived properties ────────────────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        """True when running in production environment."""
        return self.env == "production"

    @property
    def is_testing(self) -> bool:
        """True when running in test environment."""
        return self.env == "testing"

    @property
    def is_development(self) -> bool:
        """True when running in development environment."""
        return self.env == "development"
