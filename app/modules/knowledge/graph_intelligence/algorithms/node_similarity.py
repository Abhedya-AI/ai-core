"""node_similarity.py — Jaccard node similarity algorithm."""

import time

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def compute_jaccard_similarity(
    adj_list: dict[str, list[str]],
    node_a: str,
    node_b: str,
) -> IntelligenceResult:
    """Compute Jaccard similarity coefficient between two nodes based on shared neighbor sets."""
    start_time = time.perf_counter()
    nbrs_a = set(adj_list.get(node_a, []))
    nbrs_b = set(adj_list.get(node_b, []))

    intersection = nbrs_a.intersection(nbrs_b)
    union = nbrs_a.union(nbrs_b)
    sim = len(intersection) / len(union) if union else 0.0

    exec_time = int((time.perf_counter() - start_time) * 1000)

    return IntelligenceResult(
        algorithm="JaccardNodeSimilarity",
        confidence=1.0,
        execution_time_ms=exec_time,
        affected_nodes=[node_a, node_b] + list(intersection),
        affected_edges=[],
        evidence=[f"Shared neighbors: {len(intersection)}", f"Jaccard index: {sim:.4f}"],
        explanation=f"Nodes '{node_a}' and '{node_b}' have a Jaccard structural similarity of {sim:.2%}.",
        metadata={"similarity_score": sim, "shared_neighbors": list(intersection)},
    )
