"""pagerank.py — Node importance PageRank algorithm."""

import time

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def compute_pagerank(
    adj_list: dict[str, list[str]],
    damping: float = 0.85,
    max_iter: int = 20,
    tol: float = 1e-4,
) -> IntelligenceResult:
    """Compute PageRank scores for nodes in the adjacency graph."""
    start_time = time.perf_counter()
    nodes = list(set(adj_list.keys()).union({v for nbrs in adj_list.values() for v in nbrs}))
    if not nodes:
        return IntelligenceResult(algorithm="PageRank", confidence=1.0, execution_time_ms=0)

    n = len(nodes)
    ranks: dict[str, float] = {node: 1.0 / n for node in nodes}

    # Incoming edges map
    incoming: dict[str, list[str]] = {node: [] for node in nodes}
    out_degree: dict[str, int] = {node: 0 for node in nodes}

    for u, nbrs in adj_list.items():
        out_degree[u] = len(nbrs)
        for v in nbrs:
            incoming[v].append(u)

    for _ in range(max_iter):
        new_ranks: dict[str, float] = {}
        diff = 0.0
        for node in nodes:
            rank_sum = sum(
                ranks[src] / out_degree[src] for src in incoming[node] if out_degree[src] > 0
            )
            new_rank = (1.0 - damping) / n + damping * rank_sum
            diff += abs(new_rank - ranks[node])
            new_ranks[node] = new_rank
        ranks = new_ranks
        if diff < tol:
            break

    exec_time = int((time.perf_counter() - start_time) * 1000)
    top_nodes = sorted(ranks.keys(), key=lambda x: ranks[x], reverse=True)

    return IntelligenceResult(
        algorithm="PageRank",
        confidence=1.0,
        execution_time_ms=exec_time,
        affected_nodes=top_nodes[:10],
        affected_edges=[],
        evidence=[f"Top node: {top_nodes[0]} (Rank: {ranks[top_nodes[0]]:.4f})"] if top_nodes else [],
        explanation=f"PageRank calculated node importance across {n} graph entities.",
        metadata={"ranks": ranks},
    )
