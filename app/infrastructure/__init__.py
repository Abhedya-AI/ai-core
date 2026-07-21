"""
app/infrastructure/__init__.py

Shared types for the infrastructure layer.
HealthStatus is the standard return type for all check_*() functions.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class HealthStatus:
    """Standard health check result returned by every check_*() function."""

    service: str
    status: Literal["healthy", "unhealthy"]
    latency_ms: int = 0
    error: str | None = None

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"

    def to_dict(self) -> dict:
        d = {
            "service": self.service,
            "status": self.status,
            "latency_ms": self.latency_ms,
        }
        if self.error:
            d["error"] = self.error
        return d
