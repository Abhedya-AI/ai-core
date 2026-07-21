"""k_hop.py — K-Hop Neighborhood Expansion algorithm for GraphRAG context."""

import time
from collections import deque

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def k_hop_expansion(
    adj_list: dict[str, list[str]],
    center_node: str,
    k: int = 3,
) -> IntelligenceResult:
    """Expand k-hop neighborhood from center_node."""
    start_time = time.perf_counter()
    visited: dict[str, int] = {center_node: 0}
    queue = deque([(center_node, 0)])
    edges: list[str] = []

    while queue:
        current, dist = queue.popleft()
        if dist >= k:
            continue

        for neighbor in adj_list.get(current, []):
            edges.append(f"{current} -> {neighbor}")
            if neighbor not in visited:
                visited[neighbor] = dist + 1
                queue.append((neighbor, dist + 1))

    exec_time = int((time.perf_counter() - start_time) * 1000)
    nodes = list(visited.keys())

    return IntelligenceResult(
        algorithm="KHopExpansion",
        confidence=1.0,
        execution_time_ms=exec_time,
        affected_nodes=nodes,
        affected_edges=edges,
        evidence=[f"Expanded {len(nodes)} nodes up to {k} hops"],
        explanation=f"K-hop expansion extracted {len(nodes)} connected entities within {k} hops of '{center_node}'.",
        metadata={"k": k, "node_count": len(nodes)},
    )
