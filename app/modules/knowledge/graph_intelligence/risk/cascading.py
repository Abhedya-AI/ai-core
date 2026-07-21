"""cascading.py — Cascading failure simulation."""

import time

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult


def simulate_cascading_failure(
    adj_list: dict[str, list[str]],
    trigger_node_id: str,
    failure_threshold: float = 0.8,
) -> IntelligenceResult:
    """Simulate cascading failure across connected equipment/zones."""
    start_time = time.perf_counter()
    failed_nodes: list[str] = [trigger_node_id]
    queue = [trigger_node_id]
    visited = {trigger_node_id}
    edges: list[str] = []

    while queue:
        curr = queue.pop(0)
        for nxt in adj_list.get(curr, []):
            edges.append(f"{curr} -[FAILOVER]-> {nxt}")
            if nxt not in visited:
                visited.add(nxt)
                failed_nodes.append(nxt)
                queue.append(nxt)

    exec_time = int((time.perf_counter() - start_time) * 1000)

    return IntelligenceResult(
        algorithm="CascadingFailureSimulation",
        confidence=0.88,
        execution_time_ms=exec_time,
        affected_nodes=failed_nodes,
        affected_edges=edges,
        evidence=[f"Cascading failure impacted {len(failed_nodes)} entities"],
        explanation=f"Trigger failure at '{trigger_node_id}' caused cascading failure affecting {len(failed_nodes)} downstream assets.",
        metadata={"trigger_node": trigger_node_id, "failed_count": len(failed_nodes)},
    )
