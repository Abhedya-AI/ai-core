from __future__ import annotations
import math
from app.core.logging import get_logger

log = get_logger(__name__)

class BarrierModelEngine:
    """Engine for modeling physical barriers."""

    def __init__(self) -> None:
        pass

    def compute_barrier_resistance(self, barriers: list[dict]) -> float:
        """Compute combined barrier resistance."""
        if not barriers:
            return 0.0
            
        product = 1.0
        for b in barriers:
            factor = b.get("resistance_factor", 0.5)
            product *= (1.0 - factor)
            
        resistance = 1.0 - product
        return max(0.0, min(0.99, resistance))

    def get_effective_edge_resistance(self, edge_resistance: float, barrier_resistance: float) -> float:
        """Max of edge and barrier resistance."""
        return max(edge_resistance, barrier_resistance)

    def filter_barriers_for_hazard(self, barriers: list[dict], hazard_type: str) -> list[dict]:
        """Filter applicable barriers for a hazard type."""
        applicable = []
        rules = {
            "FIRE": ["FIRE_DOOR", "FIREWALL"],
            "SMOKE": ["FIRE_DOOR", "FIREWALL"],
            "EXPLOSION": ["BLAST_WALL", "BLAST_CURTAIN"],
            "HIGH_PRESSURE": ["BLAST_WALL", "BLAST_CURTAIN"],
            "GAS_LEAK": ["ISOLATION_VALVE", "SAFETY_VALVE", "VAPOUR_BARRIER"],
            "STEAM_LEAK": ["ISOLATION_VALVE", "SAFETY_VALVE"],
            "TOXIC_GAS": ["ISOLATION_VALVE", "SAFETY_VALVE", "VAPOUR_BARRIER"],
            "CHEMICAL_SPILL": ["CONTAINMENT_BUND"],
            "FLOOD": ["CONTAINMENT_BUND"]
        }
        
        allowed_types = rules.get(hazard_type, [])
        for b in barriers:
            b_type = b.get("type", "")
            if b_type in allowed_types:
                applicable.append(b)
                
        return applicable

    def estimate_barrier_deployment_time(self, barrier_types: list[str]) -> float:
        """Estimate deployment time in minutes."""
        times = {
            "SAFETY_VALVE": 2.0,
            "FIRE_DOOR": 1.0,
            "ISOLATION_VALVE": 5.0,
            "BLAST_CURTAIN": 10.0,
            "FIREWALL": 60.0,
            "BLAST_WALL": 120.0,
            "CONTAINMENT_BUND": 20.0,
            "VAPOUR_BARRIER": 30.0
        }
        return sum(times.get(bt, 0.0) for bt in barrier_types)

    def check_barrier_sufficiency(self, barriers: list[dict], required_resistance: float) -> bool:
        """Check if barriers provide enough resistance."""
        res = self.compute_barrier_resistance(barriers)
        return res >= required_resistance
