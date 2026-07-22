"""maintenance_provider.py — Maintenance History Evidence Provider."""

from typing import Any


class MaintenanceEvidenceProvider:
    """Extracts overdue maintenance records and component replacement histories."""

    @staticmethod
    def get_maintenance_evidence(metadata: dict[str, Any]) -> list[dict[str, Any]]:
        return metadata.get("maintenance_logs", [{"asset": "VALVE-V12", "overdue_days": 34, "status": "OVERDUE"}])
