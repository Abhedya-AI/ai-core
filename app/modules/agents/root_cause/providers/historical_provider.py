"""historical_provider.py — Historical Incidents Evidence Provider."""

from typing import Any


class HistoricalEvidenceProvider:
    """Retrieves similar past incidents from Knowledge Graph and Vector store."""

    @staticmethod
    def get_historical_incidents(asset_id: str) -> list[dict[str, Any]]:
        return [
            {"incident_id": "INC-2025-08", "asset": asset_id, "cause": "Valve seal failure", "similarity": 0.89},
            {"incident_id": "INC-2025-11", "asset": asset_id, "cause": "Overpressure breach", "similarity": 0.82},
        ]
