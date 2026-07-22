"""notification_provider.py — Emergency Notification Channel Provider."""

from typing import Any


class NotificationEmergencyProvider:
    """Dispatches multi-channel siren, PA system, and mobile alert notifications."""

    @staticmethod
    def get_notification_channels() -> list[str]:
        return ["SIREN_ALARM", "PA_SYSTEM", "MOBILE_PUSH", "DISPATCH_CONSOLE"]
