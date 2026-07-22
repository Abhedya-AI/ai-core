"""regulation_provider.py — Regulatory Evidence Provider."""

from typing import Any


class RegulationEvidenceProvider:
    """Provides OSHA/ISO regulatory standards relevant to incident investigation."""

    @staticmethod
    def get_regulatory_rules() -> list[dict[str, Any]]:
        return [
            {"code": "OSHA-1910.147", "title": "Lockout/Tagout Standard"},
            {"code": "ISO-45001", "title": "Occupational Health and Safety Management"},
        ]
