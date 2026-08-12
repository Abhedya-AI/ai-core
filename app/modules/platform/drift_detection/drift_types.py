from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
import uuid

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uuid() -> str:
    return str(uuid.uuid4())

class DriftReport(BaseModel):
    model_config = ConfigDict(frozen=True)
    report_id: str = Field(default_factory=_uuid)
    model_id: str = ""
    feature_name: str | None = None
    drift_type: str
    statistical_test: str
    drift_score: float
    severity: str
    drift_detected: bool
    description: str
    metrics: dict[str, float] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=_now_iso)

from enum import Enum
class DriftSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
