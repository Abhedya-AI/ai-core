from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)

HAZARD_ACTIONS = {
    "FIRE": [
        {"priority": 1, "type": "FIRE_SUPPRESSION", "action": "Activate fire suppression system", "time_minutes": 2, "operators": 2},
        {"priority": 2, "type": "BARRIER_DEPLOYMENT", "action": "Close all fire doors in adjacent zones", "time_minutes": 3, "operators": 2},
        {"priority": 3, "type": "SHUTDOWN", "action": "Shutdown ventilation fans feeding fire zone", "time_minutes": 5, "operators": 1},
        {"priority": 4, "type": "EVACUATION", "action": "Evacuate adjacent zones", "time_minutes": 10, "operators": 4},
        {"priority": 5, "type": "EMERGENCY_SERVICES", "action": "Notify fire brigade", "time_minutes": 1, "operators": 1},
    ],
    "GAS_LEAK": [
        {"priority": 1, "type": "VALVE_ISOLATION", "action": "Close upstream isolation valves", "time_minutes": 5, "operators": 2},
        {"priority": 2, "type": "VENTILATION_INCREASE", "action": "Increase zone ventilation to maximum", "time_minutes": 3, "operators": 1},
        {"priority": 3, "type": "EVACUATION", "action": "Evacuate affected zone", "time_minutes": 8, "operators": 3},
        {"priority": 4, "type": "EMERGENCY_SERVICES", "action": "Alert gas response team", "time_minutes": 2, "operators": 1},
        {"priority": 5, "type": "MONITORING", "action": "Deploy continuous gas monitors", "time_minutes": 10, "operators": 2},
    ],
    "EXPLOSION": [
        {"priority": 1, "type": "EVACUATION", "action": "Immediate blast zone evacuation", "time_minutes": 5, "operators": 5},
        {"priority": 2, "type": "SHUTDOWN", "action": "Emergency shutdown all equipment in zone", "time_minutes": 2, "operators": 2},
        {"priority": 3, "type": "EMERGENCY_SERVICES", "action": "Call emergency services", "time_minutes": 1, "operators": 1},
        {"priority": 4, "type": "BARRIER_DEPLOYMENT", "action": "Deploy blast curtains on adjacent zones", "time_minutes": 8, "operators": 3},
    ],
    "CHEMICAL_SPILL": [
        {"priority": 1, "type": "CONTAINMENT", "action": "Activate containment bunds", "time_minutes": 3, "operators": 2},
        {"priority": 2, "type": "NEUTRALIZE", "action": "Deploy chemical neutralization agent", "time_minutes": 15, "operators": 3},
        {"priority": 3, "type": "PPE_UPGRADE", "action": "Upgrade PPE to Level A for responders", "time_minutes": 10, "operators": 2},
        {"priority": 4, "type": "EMERGENCY_SERVICES", "action": "Alert hazmat response team", "time_minutes": 2, "operators": 1},
    ],
    "FLOOD": [
        {"priority": 1, "type": "VALVE_ISOLATION", "action": "Close water supply isolation valves", "time_minutes": 5, "operators": 2},
        {"priority": 2, "type": "PUMPING", "action": "Deploy submersible pumps", "time_minutes": 20, "operators": 3},
        {"priority": 3, "type": "ELECTRICAL_SHUTDOWN", "action": "Shutdown electrical systems in flood zone", "time_minutes": 3, "operators": 2},
        {"priority": 4, "type": "STRUCTURAL_CHECK", "action": "Assess structural integrity", "time_minutes": 30, "operators": 2},
    ],
    "TOXIC_GAS": [
        {"priority": 1, "type": "EVACUATION", "action": "Immediate evacuation of all personnel", "time_minutes": 5, "operators": 5},
        {"priority": 2, "type": "VALVE_ISOLATION", "action": "Isolate toxic gas source valves", "time_minutes": 5, "operators": 2},
        {"priority": 3, "type": "VENTILATION_INCREASE", "action": "Maximum forced ventilation", "time_minutes": 3, "operators": 1},
        {"priority": 4, "type": "EMERGENCY_SERVICES", "action": "Alert hazmat and medical teams", "time_minutes": 1, "operators": 1},
    ],
}

DEFAULT_ACTIONS = [
    {"priority": 1, "type": "MONITORING", "action": "Increase monitoring frequency", "time_minutes": 5, "operators": 1},
    {"priority": 2, "type": "EVACUATION", "action": "Evacuate if severity is HIGH or above", "time_minutes": 10, "operators": 3},
    {"priority": 3, "type": "EMERGENCY_SERVICES", "action": "Notify emergency response coordinator", "time_minutes": 2, "operators": 1},
]

class IsolationStrategyGenerator:
    def __init__(self, graphrag_service=None, knowledge_service=None) -> None:
        self.graphrag_service = graphrag_service
        self.knowledge_service = knowledge_service

    async def generate_isolation_strategy(
        self, propagation_id: str, hazard_type: str, source_node_id: str, 
        affected_nodes: list[str], severity: str, context: dict
    ) -> dict:
        raw_actions = self._generate_actions_for_hazard(hazard_type, affected_nodes, severity)
        prioritized = self.prioritize_actions(raw_actions, severity)
        
        # Optionally enrich
        if self.graphrag_service:
            try:
                pass
            except Exception as e:
                log.warning(f"GraphRAG enrichment failed: {e}")
                
        eff = self.estimate_isolation_effectiveness(prioritized, [], hazard_type)
        optimal_pt = self.select_optimal_isolation_point(affected_nodes, context.get("graph"))
        
        return {
            "propagation_id": propagation_id,
            "strategy_type": "CONTAINMENT",
            "actions": prioritized,
            "estimated_effectiveness": eff,
            "optimal_isolation_node": optimal_pt,
            "status": "DRAFT"
        }

    def _generate_actions_for_hazard(self, hazard_type: str, affected_nodes: list[str], severity: str) -> list[dict]:
        return list(HAZARD_ACTIONS.get(hazard_type, DEFAULT_ACTIONS))

    def prioritize_actions(self, actions: list[dict], severity: str) -> list[dict]:
        result = [dict(a) for a in actions]
        result.sort(key=lambda x: x.get("priority", 99))
        
        if severity in ("CATASTROPHIC", "CRITICAL"):
            for a in result:
                a["time_minutes"] = 0
                a["action"] = f"[IMMEDIATE] {a.get('action')}"
        elif severity == "MINOR":
            for a in result:
                a["time_minutes"] = a.get("time_minutes", 0) + 15
                a["action"] = f"[DELAYED] {a.get('action')}"
                
        return result

    def estimate_isolation_effectiveness(self, actions: list[dict], barriers: list[dict], hazard_type: str) -> float:
        base_eff = 0.3 + 0.1 * len(actions)
        barrier_boost = sum(b.get("resistance", 0.1) for b in barriers) * 0.3
        return min(0.95, max(0.0, base_eff + barrier_boost))

    def select_optimal_isolation_point(self, affected_nodes: list[str], graph: dict | None) -> str | None:
        if not affected_nodes:
            return None
        if not graph:
            return affected_nodes[0]
            
        try:
            edges = graph.get("edges", [])
            counts = {n: 0 for n in affected_nodes}
            for e in edges:
                src = e.get("source")
                dst = e.get("target")
                if src in counts:
                    counts[src] += 1
                if dst in counts:
                    counts[dst] += 1
            best = max(counts.items(), key=lambda x: x[1])
            return best[0]
        except Exception:
            return affected_nodes[0]
