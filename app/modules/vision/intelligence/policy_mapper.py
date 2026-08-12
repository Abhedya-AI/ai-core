"""
intelligence/policy_mapper.py — Safety Policy & Regulation Mapper.

Maps detected vision violations to OSHA, ISO 45001, and plant safety regulations.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

log = get_logger("vision.intelligence.policy_mapper")

POLICY_REGISTRY: dict[str, list[dict[str, str]]] = {
    "PPE": [
        {"code": "OSHA 1910.135", "title": "Head Protection Standard"},
        {"code": "OSHA 1910.136", "title": "Occupational Foot Protection"},
        {"code": "ISO 45001 Sec 8.1.2", "title": "Eliminating Hazards & Reducing OH&S Risks"},
    ],
    "RESTRICTED_ZONE": [
        {"code": "OSHA 1910.22", "title": "General Walking-Working Surfaces"},
        {"code": "PLANT-REG-Z04", "title": "Unauthorized Hazardous Area Entry Policy"},
    ],
    "UNSAFE_BEHAVIOR": [
        {"code": "OSHA 1910.178", "title": "Powered Industrial Truck Proximity"},
        {"code": "ISO 45001 Sec 6.1.2", "title": "Hazard Identification & Assessment"},
    ],
    "FALL": [
        {"code": "OSHA 1910.140", "title": "Personal Fall Protection Systems"},
        {"code": "OSHA 1910.28", "title": "Fall Protection Duty"},
    ],
    "FIRE": [
        {"code": "OSHA 1910.38", "title": "Emergency Action Plans"},
        {"code": "NFPA 101", "title": "Life Safety Code"},
    ],
}


class PolicyMapper:
    """Mapper associating violation events with safety policy standards."""

    @staticmethod
    def map_policies(violation_category: str) -> list[dict[str, str]]:
        """Return list of matching policy dictionaries."""
        cat_upper = violation_category.upper()
        for key in POLICY_REGISTRY:
            if key in cat_upper:
                return POLICY_REGISTRY[key]
        return [{"code": "GEN-SAFETY-01", "title": "General Industrial Workplace Safety Standard"}]
