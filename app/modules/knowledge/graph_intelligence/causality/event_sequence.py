"""event_sequence.py — Chronological event sequence generator."""

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def generate_event_sequence(events: list[dict]) -> IntelligenceResult:
    """Build chronological event timeline."""
    sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""))
    return IntelligenceResult(
        algorithm="EventSequence",
        confidence=1.0,
        execution_time_ms=1,
        affected_nodes=[e.get("id", "") for e in sorted_events],
        explanation=f"Built chronological sequence of {len(sorted_events)} events.",
        metadata={"sequence": sorted_events},
    )
