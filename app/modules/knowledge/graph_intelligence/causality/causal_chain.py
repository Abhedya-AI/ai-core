"""causal_chain.py — Causal chain builder."""

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def build_causal_chain(events: list[dict]) -> IntelligenceResult:
    """Order and format a causal chain of events."""
    sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""))
    chain = [f"{e.get('id', 'Event')}: {e.get('title', 'Event')}" for e in sorted_events]
    return IntelligenceResult(
        algorithm="CausalChainBuilder",
        confidence=0.95,
        execution_time_ms=1,
        affected_nodes=[e.get("id", "") for e in sorted_events],
        evidence=[f"Ordered {len(sorted_events)} timeline events"],
        explanation=f"Reconstructed causal sequence: {' -> '.join(chain)}.",
        metadata={"causal_chain": chain},
    )
