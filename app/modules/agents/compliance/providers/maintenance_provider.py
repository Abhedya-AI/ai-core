"""maintenance_provider.py — Maintenance Compliance Evidence Provider."""

from typing import Any


class MaintenanceComplianceProvider:
    """Extracts equipment maintenance inspection logs."""

    @staticmethod
    def get_maintenance(metadata: dict[str, Any]) -> list[dict[str, Any]]:
        return metadata.get(
            "maintenance_records",
            [{"asset_id": "EQ-PUMP-7", "inspection_overdue": True, "overdue_days": 18}],
        )
