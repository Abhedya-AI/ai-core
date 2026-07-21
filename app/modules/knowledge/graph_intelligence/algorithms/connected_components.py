"""connected_components.py — Connected components discovery."""

import time

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def find_connected_components(adj_list: dict[str, list[str]]) -> IntelligenceResult:
    """Find all connected components in an undirected view of the graph."""
    start_time = time.perf_counter()
    # Build undirected graph
    undirected: dict[str, set[str]] = {}
    all_nodes = set(adj_list.keys())
    for u, neighbors in adj_list.items():
        undirected.setdefault(u, set())
        for v in neighbors:
            undirected[u].add(v)
            undirected.setdefault(v, set()).add(u)
            all_nodes.add(v)

    visited: set[str] = set()
    components: list[list[str]] = []

    for node in all_nodes:
        if node not in visited:
            comp: list[str] = []
            stack = [node]
            visited.add(node)
            while stack:
                curr = stack.pop()
                comp.append(curr)
                for nxt in undirected.get(curr, set()):
                    if nxt not in visited:
                        visited.add(nxt)
                        stack.append(nxt)
            components.append(comp)

    exec_time = int((time.perf_counter() - start_time) * 1000)
    largest_comp = max(components, key=len) if components else []

    return IntelligenceResult(
        algorithm="ConnectedComponents",
        confidence=1.0,
        execution_time_ms=exec_time,
        affected_nodes=largest_comp,
        affected_edges=[],
        evidence=[f"Found {len(components)} connected components"],
        explanation=f"Identified {len(components)} isolated/connected clusters in the facility graph.",
        metadata={"num_components": len(components), "component_sizes": [len(c) for c in components]},
    )
