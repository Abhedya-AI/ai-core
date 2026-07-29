"""
application/__init__.py — Application layer public API.

Re-exports the canonical entry points so callers can do:

    from app.modules.vision.application import ProcessDetectionUseCase
    from app.modules.vision.application import VisionOrchestrator
    from app.modules.vision.application import FrameAnalysisResult

Structure
─────────
  application/
  ├── use_cases/          — individual single-responsibility use cases
  ├── dto/                — FrameAnalysisResult + request aliases
  ├── services/           — VisionOrchestrator (long-lived service)
  ├── exceptions.py       — custom exception hierarchy
  ├── calculate_risk.py   — RiskEngine (domain algorithm, stays at root)
  ├── publish_event.py    — Kafka publisher function (stays at root)
  ├── analyze_frame.py    — shim → use_cases/analyze_frame.py
  └── save_detection.py   — shim → use_cases/save_detection.py
"""

# ── Use cases ──────────────────────────────────────────────────────────────────
from app.modules.vision.application.use_cases.analyze_frame import (
    AnalyzeFrameUseCase,
    FrameDetector,
)
from app.modules.vision.application.use_cases.calculate_risk import CalculateRiskUseCase
from app.modules.vision.application.use_cases.publish_event import PublishEventUseCase
from app.modules.vision.application.use_cases.save_detection import SaveDetectionUseCase
from app.modules.vision.application.use_cases.process_detection import (
    ProcessDetectionUseCase,
)

# ── DTOs ──────────────────────────────────────────────────────────────────────
from app.modules.vision.application.dto.analyze_response import FrameAnalysisResult

# ── Services ──────────────────────────────────────────────────────────────────
from app.modules.vision.application.services.vision_orchestrator import (
    VisionOrchestrator,
)

# ── Exceptions ────────────────────────────────────────────────────────────────
from app.modules.vision.application.exceptions import (
    VisionError,
    FrameReadError,
    DetectorUnavailableError,
    RiskCalculationError,
    PersistenceError,
    EventPublishingError,
)

# ── Domain algorithms (kept at root for backwards compat) ──────────────────────
from app.modules.vision.application.calculate_risk import RiskEngine
from app.modules.vision.application.publish_event import (
    PublishEventError,
    publish_vision_event,
)

__all__ = [
    # Use cases
    "AnalyzeFrameUseCase",
    "FrameDetector",
    "CalculateRiskUseCase",
    "SaveDetectionUseCase",
    "PublishEventUseCase",
    "ProcessDetectionUseCase",
    # DTOs
    "FrameAnalysisResult",
    # Services
    "VisionOrchestrator",
    # Exceptions
    "VisionError",
    "FrameReadError",
    "DetectorUnavailableError",
    "RiskCalculationError",
    "PersistenceError",
    "EventPublishingError",
    # Legacy / backwards compat
    "RiskEngine",
    "publish_vision_event",
    "PublishEventError",
]
