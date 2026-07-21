"""temporal_reasoning.py — Temporal graph reasoning module."""

from datetime import datetime, timezone

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def evaluate_temporal_state(node_validity: dict[str, tuple[datetime | None, datetime | None]], target_time: datetime) -> IntelligenceResult:
    """Filter nodes that were active/valid at a specific historical point in time."""
    active_nodes = []
    for node_id, (v_from, v_to) in node_validity.items():
        if (v_from is None or v_from <= target_time) and (v_to is None or v_to >= target_time):
            active_nodes.append(node_id)

    return IntelligenceResult(
        algorithm="TemporalReasoning",
        confidence=1.0,
        execution_time_ms=1,
        affected_nodes=active_nodes,
        evidence=[f"Evaluated state at {target_time.isoformat()}"],
        explanation=f"Reconstructed plant state at {target_time.isoformat()}: {len(active_nodes)} active entities.",
        metadata={"active_count": len(active_nodes), "target_time": target_time.isoformat()},
    )
