"""centrality.py — Degree and closeness centrality metrics."""

import time

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def compute_centrality(adj_list: dict[str, list[str]]) -> IntelligenceResult:
    """Compute degree centrality for graph nodes."""
    start_time = time.perf_counter()
    in_degree: dict[str, int] = {}
    out_degree: dict[str, int] = {}
    all_nodes = set(adj_list.keys())

    for u, nbrs in adj_list.items():
        out_degree[u] = len(nbrs)
        for v in nbrs:
            in_degree[v] = in_degree.get(v, 0) + 1
            all_nodes.add(v)

    total_degree = {node: in_degree.get(node, 0) + out_degree.get(node, 0) for node in all_nodes}
    exec_time = int((time.perf_counter() - start_time) * 1000)
    sorted_nodes = sorted(total_degree.keys(), key=lambda x: total_degree[x], reverse=True)

    return IntelligenceResult(
        algorithm="Centrality",
        confidence=1.0,
        execution_time_ms=exec_time,
        affected_nodes=sorted_nodes[:10],
        affected_edges=[],
        evidence=[f"Highest degree node: {sorted_nodes[0]} (Degree: {total_degree[sorted_nodes[0]]})"] if sorted_nodes else [],
        explanation=f"Centrality metrics identified key hub nodes in the facility graph.",
        metadata={"total_degree": total_degree},
    )
