"""exceptions.py — Notification Agent Domain Exceptions."""


class NotificationError(Exception):
    """Base exception for all Notification Agent errors."""


class TemplateNotFoundError(NotificationError):
    """Raised when no template is found for a domain event type."""

    def __init__(self, event_type: str) -> None:
        super().__init__(f"No template registered for event type: '{event_type}'")
        self.event_type = event_type


class RecipientResolutionError(NotificationError):
    """Raised when no recipients can be resolved for an event."""

    def __init__(self, event_type: str) -> None:
        super().__init__(f"No recipients resolved for event type: '{event_type}'")
        self.event_type = event_type


class ProviderError(NotificationError):
    """Raised when a notification provider fails to deliver a message."""

    def __init__(self, channel: str, reason: str) -> None:
        super().__init__(f"Provider '{channel}' failed: {reason}")
        self.channel = channel
        self.reason = reason


class RateLimitExceededError(NotificationError):
    """Raised when a recipient exceeds the allowed notification rate."""

    def __init__(self, recipient_id: str, channel: str) -> None:
        super().__init__(f"Rate limit exceeded for recipient '{recipient_id}' on channel '{channel}'")
        self.recipient_id = recipient_id
        self.channel = channel


class PolicyViolationError(NotificationError):
    """Raised when a notification attempt violates an active policy."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Policy violation: {reason}")
        self.reason = reason
