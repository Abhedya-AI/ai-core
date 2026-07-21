"""community_detection.py — Community detection algorithm (Label Propagation)."""

import time

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def detect_communities(adj_list: dict[str, list[str]], max_iter: int = 10) -> IntelligenceResult:
    """Detect node communities using Label Propagation algorithm."""
    start_time = time.perf_counter()
    all_nodes = set(adj_list.keys())
    for nbrs in adj_list.values():
        all_nodes.update(nbrs)

    labels: dict[str, str] = {node: node for node in all_nodes}

    # Undirected neighbor map for label propagation
    undirected: dict[str, set[str]] = {node: set() for node in all_nodes}
    for u, nbrs in adj_list.items():
        for v in nbrs:
            undirected[u].add(v)
            undirected[v].add(u)

    for _ in range(max_iter):
        changed = False
        for node in all_nodes:
            nbr_labels = [labels[nbr] for nbr in undirected[node]]
            if nbr_labels:
                most_frequent = max(set(nbr_labels), key=nbr_labels.count)
                if labels[node] != most_frequent:
                    labels[node] = most_frequent
                    changed = True
        if not changed:
            break

    # Group nodes by community label
    communities: dict[str, list[str]] = {}
    for node, comm_id in labels.items():
        communities.setdefault(comm_id, []).append(node)

    exec_time = int((time.perf_counter() - start_time) * 1000)

    return IntelligenceResult(
        algorithm="CommunityDetection",
        confidence=1.0,
        execution_time_ms=exec_time,
        affected_nodes=list(all_nodes),
        affected_edges=[],
        evidence=[f"Detected {len(communities)} communities"],
        explanation=f"Grouped facility entities into {len(communities)} operational communities.",
        metadata={"communities": communities},
    )
