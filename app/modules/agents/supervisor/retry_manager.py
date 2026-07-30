"""retry_manager.py — Transient vs Non-Transient Retry Manager.

Classification rules:
  - Retryable (transient): Timeout, ConnectionError, RateLimitError, TemporaryGraphError
  - Non-Retryable: ValidationError, OntologyViolation, SchemaError, KeyError

Applies exponential backoff with jitter.
"""

import random
import time
from typing import Callable

from app.core.logging import get_logger

log = get_logger("agents.supervisor.retry_manager")

_NON_RETRYABLE_KEYWORDS = (
    "validation", "schema", "keyerror", "valueerror",
    "ontology", "typeerror", "permission", "not found",
)


class RetryManager:
    """
    Manages stage/agent execution retries with exponential backoff and jitter.
    Never retries non-transient errors.
    """

    def __init__(
        self,
        max_retries: int = 2,
        base_backoff_sec: float = 0.2,
        max_backoff_sec: float = 2.0,
    ) -> None:
        self.max_retries = max_retries
        self.base_backoff_sec = base_backoff_sec
        self.max_backoff_sec = max_backoff_sec

    def is_retryable(self, exception: Exception) -> bool:
        """
        Classify whether an exception is transient (retryable) or fatal.

        Args:
            exception: Raised exception instance.

        Returns:
            True if transient/retryable, False if non-retryable.
        """
        msg = str(exception).lower()
        exc_type = type(exception).__name__.lower()

        # Non-retryable check
        if any(kw in msg or kw in exc_type for kw in _NON_RETRYABLE_KEYWORDS):
            log.warning(f"RetryManager: non-retryable failure detected ({exc_type}: '{str(exception)[:80]}')")
            return False

        log.info(f"RetryManager: transient failure classified ({exc_type}) — retry permitted")
        return True

    def calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff duration with full jitter."""
        exponential = self.base_backoff_sec * (2 ** (attempt - 1))
        capped = min(exponential, self.max_backoff_sec)
        jittered = random.uniform(0.5 * capped, 1.5 * capped)  # noqa: S311
        return round(jittered, 3)
