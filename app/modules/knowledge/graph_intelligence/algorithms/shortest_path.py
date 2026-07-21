"""shortest_path.py — Shortest path algorithm (Dijkstra / Unweighted BFS path)."""

import time
from collections import deque

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def find_shortest_path_algo(
    adj_list: dict[str, list[str]],
    start_node: str,
    target_node: str,
) -> IntelligenceResult:
    """Find the shortest path between start_node and target_node."""
    start_time = time.perf_counter()
    queue = deque([[start_node]])
    visited = {start_node}
    found_path: list[str] = []

    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == target_node:
            found_path = path
            break

        for neighbor in adj_list.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                new_path = list(path)
                new_path.append(neighbor)
                queue.append(new_path)

    exec_time = int((time.perf_counter() - start_time) * 1000)
    edges = [f"{found_path[i]} -> {found_path[i+1]}" for i in range(len(found_path) - 1)] if found_path else []

    return IntelligenceResult(
        algorithm="ShortestPath",
        confidence=1.0 if found_path else 0.0,
        execution_time_ms=exec_time,
        affected_nodes=found_path,
        affected_edges=edges,
        evidence=[f"Path length: {len(found_path) - 1} hops"] if found_path else ["No path found"],
        explanation=f"Shortest path from '{start_node}' to '{target_node}' has {len(edges)} hops." if found_path else f"No connection path exists between '{start_node}' and '{target_node}'.",
        metadata={"path_length": max(0, len(found_path) - 1)},
    )
