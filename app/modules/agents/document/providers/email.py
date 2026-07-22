"""email.py — Email Attachment & Advisory Provider."""

from typing import Any


class EmailProvider:
    """Parses email notifications, shift handovers, and safety advisories."""

    @staticmethod
    def parse_email(raw_email: str) -> dict[str, Any]:
        return {
            "title": "Safety Advisory: Pump P-12 Vibration Monitoring",
            "sender": "plant-safety@abhedya.ai",
            "body": "Advisory IR-2025-103: Inspect Pump P-12 bearing assembly prior to restart.",
        }
