"""dfs.py — Depth-First Search (DFS) graph algorithm."""

import time

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def dfs_traversal(
    adj_list: dict[str, list[str]],
    start_node: str,
    max_depth: int = 5,
) -> IntelligenceResult:
    """Execute Depth-First Search to discover dependency chains and deep paths."""
    start_time = time.perf_counter()
    visited: set[str] = set()
    visited_nodes: list[str] = []
    edges: list[str] = []

    def _dfs(node: str, depth: int):
        if depth > max_depth or node in visited:
            return
        visited.add(node)
        visited_nodes.append(node)
        for neighbor in adj_list.get(node, []):
            edges.append(f"{node} -> {neighbor}")
            _dfs(neighbor, depth + 1)

    _dfs(start_node, 0)
    exec_time = int((time.perf_counter() - start_time) * 1000)

    return IntelligenceResult(
        algorithm="DFS",
        confidence=1.0,
        execution_time_ms=exec_time,
        affected_nodes=visited_nodes,
        affected_edges=edges,
        evidence=[f"Traversed {len(visited_nodes)} nodes recursively"],
        explanation=f"DFS discovered deep path chain of {len(visited_nodes)} nodes starting from '{start_node}'.",
        metadata={"visited_count": len(visited_nodes)},
    )
