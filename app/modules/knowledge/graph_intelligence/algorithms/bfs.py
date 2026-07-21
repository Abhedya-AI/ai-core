"""bfs.py — Breadth-First Search (BFS) graph algorithm."""

import time
from collections import deque
from typing import Any, Callable

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def bfs_traversal(
    adj_list: dict[str, list[str]],
    start_node: str,
    max_depth: int = 3,
    filter_fn: Callable[[str], bool] | None = None,
) -> IntelligenceResult:
    """
    Execute Breadth-First Search on an adjacency list.

    Args:
        adj_list: Adjacency list mapping node_id -> list of neighbor node_ids.
        start_node: Root node ID.
        max_depth: Maximum depth limit for traversal.
        filter_fn: Optional filter predicate on node_ids.

    Returns:
        IntelligenceResult containing visited nodes and BFS execution metrics.
    """
    start_time = time.perf_counter()
    visited: set[str] = {start_node}
    queue: deque[tuple[str, int]] = deque([(start_node, 0)])
    visited_nodes: list[str] = [start_node]
    edges_traversed: list[str] = []

    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue

        for neighbor in adj_list.get(current, []):
            if filter_fn and not filter_fn(neighbor):
                continue

            edges_traversed.append(f"{current} -> {neighbor}")
            if neighbor not in visited:
                visited.add(neighbor)
                visited_nodes.append(neighbor)
                queue.append((neighbor, depth + 1))

    exec_time = int((time.perf_counter() - start_time) * 1000)
    return IntelligenceResult(
        algorithm="BFS",
        confidence=1.0,
        execution_time_ms=exec_time,
        affected_nodes=visited_nodes,
        affected_edges=edges_traversed,
        evidence=[f"Explored {len(visited_nodes)} nodes up to depth {max_depth}"],
        explanation=f"BFS expanded {len(visited_nodes)} nodes within a {max_depth}-hop radius starting from '{start_node}'.",
        metadata={"visited_count": len(visited_nodes), "depth_limit": max_depth},
    )
