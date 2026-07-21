"""graph_ranker.py — Graph topology distance ranker."""

from typing import Any


def rank_graph_facts_by_distance(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank graph facts by graph hop distance."""
    return sorted(facts, key=lambda x: x.get("_hop_depth", 0))
