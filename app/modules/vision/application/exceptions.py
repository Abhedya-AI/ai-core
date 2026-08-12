"""
application/exceptions.py — Custom exception hierarchy for the Vision module.

Design principle
────────────────
Every failure mode in the application layer has a named exception.
This means:
  • Routes catch specific exceptions → specific HTTP status codes.
  • Logs are precise.
  • Unit tests assert the right exception type, not a generic message.

Hierarchy
─────────
VisionError
├── FrameReadError          — image bytes are corrupt / empty
├── DetectorUnavailableError — YOLO model not loaded or crashed
├── RiskCalculationError     — bug in RiskEngine (should never happen in prod)
├── PersistenceError         — database write failed
└── EventPublishingError     — Kafka publish failed
"""

from __future__ import annotations


class VisionError(Exception):
    """
    Base class for all Vision module application errors.

    Attributes
    ──────────
    message     Human-readable error description.
    detail      Optional structured context (dict or str).
    """

    def __init__(self, message: str, detail: object = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail  = detail

    def __repr__(self) -> str:
        return f"{type(self).__name__}(message={self.message!r})"


# ── Frame / image errors ───────────────────────────────────────────────────────

class FrameReadError(VisionError):
    """
    Raised when the incoming image bytes cannot be read or decoded.

    Typical causes
    ──────────────
    • Empty upload.
    • Corrupt file (truncated JPEG, unsupported codec).
    • File exceeds size limit before decoding.
    """


# ── Detector errors ────────────────────────────────────────────────────────────

class DetectorUnavailableError(VisionError):
    """
    Raised when the vision detector cannot process a frame.

    Typical causes
    ──────────────
    • YOLO model not yet loaded (cold start).
    • GPU OOM during inference.
    • Model file missing or corrupted.
    """


# ── Risk calculation errors ────────────────────────────────────────────────────

class RiskCalculationError(VisionError):
    """
    Raised when the RiskEngine fails to produce a valid score.

    This should be extremely rare in production. It typically indicates
    a programming error (e.g. unexpected HazardType added without updating
    the weight table).
    """


# ── Persistence errors ─────────────────────────────────────────────────────────

class PersistenceError(VisionError):
    """
    Raised when a repository write (save_event, save_detection) fails.

    Typical causes
    ──────────────
    • Database connection dropped.
    • Unique constraint violation (duplicate event_id).
    • Schema mismatch after migration.
    """


# ── Event publishing errors ────────────────────────────────────────────────────

class EventPublishingError(VisionError):
    """
    Raised when publishing a VisionEvent to Kafka fails.

    Typical causes
    ──────────────
    • Kafka broker unreachable.
    • Topic does not exist and auto-creation is disabled.
    • Serialisation failure.

    Note: PublishEventError in publish_event.py is a lightweight alias
    kept for backward compatibility. New code should raise this class.
    """
