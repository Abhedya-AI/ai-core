"""regulation_matcher.py — Phase 5: Dynamic Regulation Matching Engine."""

from typing import Any


class RegulationMatcher:
    """Phase 5: Maps graph entities and operational hazards to applicable OSHA/ISO regulatory standards."""

    @staticmethod
    def match_regulations(operation_query: str, entities: list[str]) -> list[str]:
        """
        Match applicable regulations.

        Returns:
            list of regulation code strings.
        """
        matched = ["OSHA-1910.147"]
        q_lower = operation_query.lower()

        if any(w in q_lower for w in ["hot work", "weld", "spark", "flame"]):
            matched.append("FS-17")
        if any(w in q_lower for w in ["confined", "tank", "vessel"]):
            matched.append("HS-04")
        if any(w in q_lower for w in ["chemical", "gas", "psm"]):
            matched.append("OSHA-1910.119")

        return list(dict.fromkeys(matched))
