"""permit_provider.py — Work Permit Evidence Provider."""

from typing import Any


class PermitProvider:
    """Extracts active and historical work permits."""

    @staticmethod
    def get_permits(metadata: dict[str, Any]) -> list[dict[str, Any]]:
        return metadata.get(
            "permits",
            [
                {
                    "permit_id": "PERMIT-HOTWORK-102",
                    "type": "HOT_WORK",
                    "expired": True,
                    "approved_by_supervisor": True,
                    "gas_test_valid": False,
                    "zone_id": "ZONE-B",
                }
            ],
        )
