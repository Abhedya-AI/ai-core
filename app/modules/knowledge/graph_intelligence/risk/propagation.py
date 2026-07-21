"""propagation.py — Risk propagation along graph edges."""

import time
from collections import deque
from typing import Any

from app.modules.knowledge.graph_intelligence.dto import IntelligenceResult, RiskAnalysisReport


def propagate_risk(
    adj_list: dict[str, list[str]],
    root_hazard_id: str,
    initial_risk: float = 100.0,
    attenuation_factor: float = 0.7,
    max_hops: int = 4,
) -> RiskAnalysisReport:
    """
    Propagate risk score starting from root_hazard_id along graph edges with attenuation.

    Args:
        adj_list: Graph adjacency map.
        root_hazard_id: Root hazard node ID.
        initial_risk: Initial risk intensity (0-100).
        attenuation_factor: Decay multiplier per hop (default: 0.7).
        max_hops: Maximum propagation distance.

    Returns:
        RiskAnalysisReport detailing risk scores per node and total affected radius.
    """
    start_time = time.perf_counter()
    risk_scores: dict[str, float] = {root_hazard_id: initial_risk}
    queue = deque([(root_hazard_id, initial_risk, 0)])
    edges: list[str] = []

    while queue:
        current, curr_risk, hop = queue.popleft()
        if hop >= max_hops or curr_risk < 1.0:
            continue

        next_risk = curr_risk * attenuation_factor
        for neighbor in adj_list.get(current, []):
            edges.append(f"{current} -[PROPAGATES_RISK]-> {neighbor}")
            if neighbor not in risk_scores or next_risk > risk_scores[neighbor]:
                risk_scores[neighbor] = round(next_risk, 2)
                queue.append((neighbor, next_risk, hop + 1))

    exec_time = int((time.perf_counter() - start_time) * 1000)
    affected_nodes = list(risk_scores.keys())

    intel_result = IntelligenceResult(
        algorithm="RiskPropagation",
        confidence=0.92,
        execution_time_ms=exec_time,
        affected_nodes=affected_nodes,
        affected_edges=edges,
        evidence=[f"Propagated risk to {len(affected_nodes)} nodes within {max_hops} hops"],
        explanation=(
            f"Risk from Hazard '{root_hazard_id}' propagated to {len(affected_nodes)} connected entities. "
            f"Max risk intensity: {initial_risk}, attenuation factor: {attenuation_factor}."
        ),
        metadata={"root_hazard_id": root_hazard_id, "scores": risk_scores},
    )

    return RiskAnalysisReport(
        root_hazard_id=root_hazard_id,
        max_risk_score=initial_risk,
        propagated_risk_scores=risk_scores,
        affected_node_ids=affected_nodes,
        risk_radius_hops=max_hops,
        intelligence_result=intel_result,
    )
