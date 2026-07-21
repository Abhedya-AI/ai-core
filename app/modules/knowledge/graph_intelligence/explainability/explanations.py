"""
explanations.py — Human-readable Explainable AI (XAI) generator.

Converts graph structures, risk propagation metrics, and causal paths
into human-understandable explanations for industrial operators and safety engineers.
"""

from typing import Any


def format_risk_explanation(
    target_node_id: str,
    risk_score: float,
    root_hazard: str | None,
    contributing_factors: list[str],
) -> str:
    """Format a human-readable explanation of why a node has a specific risk score."""
    lines = [f"Risk Assessment for Node '{target_node_id}':"]
    lines.append(f"• Overall Risk Score: {risk_score}/100")
    if root_hazard:
        lines.append(f"• Originating Hazard: {root_hazard}")

    if contributing_factors:
        lines.append("• Contributing Graph Invariants:")
        for factor in contributing_factors:
            lines.append(f"  - {factor}")

    return "\n".join(lines)


def format_causal_explanation(
    incident_id: str,
    root_causes: list[str],
    causal_path: list[str],
) -> str:
    """Format a human-readable incident root cause analysis explanation."""
    lines = [f"Root Cause Explanation for Incident '{incident_id}':"]
    lines.append(f"• Primary Candidate Root Cause(s): {', '.join(root_causes)}")
    lines.append("• Reconstructed Causal Sequence:")
    lines.append(f"  {' -> '.join(causal_path)}")
    return "\n".join(lines)
