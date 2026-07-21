"""reasoning_path.py — Step-by-step reasoning path builder."""

from typing import Any


def build_reasoning_steps(nodes: list[str], edges: list[str]) -> list[str]:
    """Construct step-by-step audit trail for explainability."""
    steps = []
    for idx in range(len(nodes) - 1):
        rel = edges[idx] if idx < len(edges) else "CONNECTED_TO"
        steps.append(f"Step {idx + 1}: {nodes[idx]} [{rel}] {nodes[idx + 1]}")
    return steps
