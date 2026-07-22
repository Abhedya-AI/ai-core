"""regulation_provider.py — Safety Regulation Evidence Provider."""

from typing import Any


class RegulationProvider:
    """Provides applicable OSHA, ISO, and Factory Safety (FS) regulations."""

    @staticmethod
    def get_regulations() -> list[dict[str, Any]]:
        return [
            {"code": "OSHA-1910.147", "title": "Control of Hazardous Energy (Lockout/Tagout)"},
            {"code": "OSHA-1910.119", "title": "Process Safety Management of Highly Hazardous Chemicals"},
            {"code": "FS-17", "title": "Factory Safety Rule: Hot Work Permit Requirements"},
            {"code": "HS-04", "title": "Confined Space Entry Standard Operating Procedure"},
        ]
