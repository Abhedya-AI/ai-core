"""topological_sort.py — Topological Sort for dependency DAGs."""

import time
from collections import deque

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def topological_sort_dag(adj_list: dict[str, list[str]]) -> IntelligenceResult:
    """Perform topological sort on a directed acyclic dependency graph."""
    start_time = time.perf_counter()
    all_nodes = set(adj_list.keys())
    for nbrs in adj_list.values():
        all_nodes.update(nbrs)

    in_degree: dict[str, int] = {node: 0 for node in all_nodes}
    for u, nbrs in adj_list.items():
        for v in nbrs:
            in_degree[v] += 1

    queue = deque([node for node in all_nodes if in_degree[node] == 0])
    topo_order: list[str] = []

    while queue:
        curr = queue.popleft()
        topo_order.append(curr)
        for nxt in adj_list.get(curr, []):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    exec_time = int((time.perf_counter() - start_time) * 1000)
    is_dag = len(topo_order) == len(all_nodes)

    return IntelligenceResult(
        algorithm="TopologicalSort",
        confidence=1.0 if is_dag else 0.5,
        execution_time_ms=exec_time,
        affected_nodes=topo_order,
        affected_edges=[],
        evidence=[f"Sorted {len(topo_order)} nodes topologically"],
        explanation="Computed topological execution/dependency sequence." if is_dag else "Graph contains cycles; partial topological ordering returned.",
        metadata={"is_dag": is_dag, "order": topo_order},
    )
