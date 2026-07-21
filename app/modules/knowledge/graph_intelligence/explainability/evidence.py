"""evidence.py — Graph evidence collector."""

from typing import Any


def collect_evidence(nodes_data: list[dict[str, Any]]) -> list[str]:
    """Collect key evidence attributes from node property dictionaries."""
    evidence = []
    for n in nodes_data:
        n_type = n.get("entity_type", "Entity")
        n_id = n.get("id", "Unknown")
        n_status = n.get("status") or n.get("severity") or n.get("role")
        if n_status:
            evidence.append(f"{n_type} '{n_id}' status/state: {n_status}")
        else:
            evidence.append(f"Involved {n_type} '{n_id}'")
    return evidence
