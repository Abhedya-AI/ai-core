"""root_cause.py — Root Cause Analysis Engine."""

import time
from collections import deque
from typing import Any

from app.modules.knowledge.graph_intelligence.dto import CausalReport, IntelligenceResult


def find_root_causes(
    incoming_adj_list: dict[str, list[str]],
    incident_node_id: str,
    max_depth: int = 6,
) -> CausalReport:
    """
    Reconstruct upstream root causes of an incident by traversing incoming causality edges
    (e.g., Sensor Failure -> Pressure Breach -> Valve Leak -> Explosion).

    Args:
        incoming_adj_list: Map of target_id -> list of source_ids (incoming edges).
        incident_node_id: ID of the incident/failure node.
        max_depth: Maximum backward search depth.

    Returns:
        CausalReport containing root causes, causal path, and evidence.
    """
    start_time = time.perf_counter()
    queue = deque([[incident_node_id]])
    visited = {incident_node_id}
    causal_paths: list[list[str]] = []
    candidate_root_causes: list[str] = []

    while queue:
        path = queue.popleft()
        current = path[-1]

        parents = incoming_adj_list.get(current, [])
        if not parents or len(path) >= max_depth:
            # Reached a source node with no incoming cause — candidate root cause!
            causal_paths.append(list(reversed(path)))
            if current not in candidate_root_causes and current != incident_node_id:
                candidate_root_causes.append(current)
            continue

        for p in parents:
            if p not in visited:
                visited.add(p)
                new_path = list(path)
                new_path.append(p)
                queue.append(new_path)

    exec_time = int((time.perf_counter() - start_time) * 1000)
    primary_causal_path = causal_paths[0] if causal_paths else [incident_node_id]

    intel_result = IntelligenceResult(
        algorithm="RootCauseAnalysis",
        confidence=0.91 if candidate_root_causes else 0.5,
        execution_time_ms=exec_time,
        affected_nodes=primary_causal_path,
        affected_edges=[f"{primary_causal_path[i]} -[CAUSES]-> {primary_causal_path[i+1]}" for i in range(len(primary_causal_path) - 1)],
        evidence=[
            f"Candidate Root Causes: {candidate_root_causes}",
            f"Primary Causal Path: {' -> '.join(primary_causal_path)}",
        ],
        explanation=(
            f"Root cause analysis for Incident '{incident_node_id}' identified "
            f"{len(candidate_root_causes)} potential root causes: {candidate_root_causes}. "
            f"Primary causal sequence: {' -> '.join(primary_causal_path)}."
        ),
        metadata={
            "incident_id": incident_node_id,
            "root_causes": candidate_root_causes,
            "causal_path": primary_causal_path,
        },
    )

    return CausalReport(
        target_incident_id=incident_node_id,
        candidate_root_causes=candidate_root_causes,
        causal_path=primary_causal_path,
        timeline_events=[],
        intelligence_result=intel_result,
    )
