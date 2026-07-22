"""sop_provider.py — Standard Operating Procedure Evidence Provider."""

from typing import Any


class SOPProvider:
    """Provides SOP step sequence rules and execution tracking logs."""

    @staticmethod
    def get_sops(metadata: dict[str, Any]) -> list[dict[str, Any]]:
        return metadata.get(
            "sops",
            [
                {
                    "sop_id": "SOP-LOCKOUT-01",
                    "title": "Hazardous Energy Lockout/Tagout",
                    "required_sequence": ["Shutdown", "Isolation", "Lockout", "Verification", "Maintenance"],
                    "executed_sequence": ["Shutdown", "Isolation", "Maintenance"],
                }
            ],
        )
