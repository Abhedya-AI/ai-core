from __future__ import annotations
import uuid
from datetime import datetime, timezone
import numpy as np
import networkx as nx

from app.core.logging import get_logger
log = get_logger(__name__)

try:
    from app.modules.knowledge.services.knowledge_service import KnowledgeService
except ImportError:
    KnowledgeService = None

class HazardPropagationForecaster:
    """Forecaster for predicting how hazards spread across physical or logical zones."""

    def __init__(self, knowledge_service=None) -> None:
        self.knowledge_service = knowledge_service
        self.decay_factor = 0.8  # Default exponential decay by distance

    async def forecast_propagation(self, hazard_id: str, zone_ids: list[str], horizon_hours: int) -> dict:
        """Forecast the propagation of a hazard over a specified horizon."""
        log.info(f"Forecasting hazard {hazard_id} propagation for {horizon_hours} hours")
        
        # In a real implementation, we would query knowledge_service for zone adjacency.
        # Here we mock an adjacency based on zone_ids for the algorithm
        adjacency = {}
        for i, z in enumerate(zone_ids):
            adjacency[z] = []
            if i > 0:
                adjacency[z].append((zone_ids[i-1], 1.0))
            if i < len(zone_ids) - 1:
                adjacency[z].append((zone_ids[i+1], 1.0))
                
        transition_matrix = self._compute_propagation_matrix(adjacency)
        
        initial_zones = {z: (1.0 if i == 0 else 0.0) for i, z in enumerate(zone_ids)}
        
        probabilities = self._simulate_spread(initial_zones, horizon_hours, transition_matrix)
        
        affected = [z for z, p in probabilities.items() if p > 0.1]
        
        # Sort by propagation likelihood
        sorted_zones = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        propagation_path = [z for z, p in sorted_zones if p > 0.05]
        
        max_prob = max(probabilities.values()) if probabilities else 0.0
        escalation_risk = float(np.clip(max_prob * len(affected) / max(len(zone_ids), 1), 0.0, 1.0))
        containment_hours = float(np.clip(24.0 * (1.0 - escalation_risk), 1.0, 72.0))
        
        return {
            "propagation_probability": probabilities,
            "affected_zones": affected,
            "containment_hours": containment_hours,
            "escalation_risk": escalation_risk,
            "propagation_path": propagation_path
        }

    def _compute_propagation_matrix(self, adjacency: dict) -> np.ndarray:
        """Compute the propagation transition matrix."""
        zones = list(adjacency.keys())
        n = len(zones)
        matrix = np.zeros((n, n))
        
        for i, z1 in enumerate(zones):
            matrix[i, i] = 1.0  # Self retention
            for z2, dist in adjacency.get(z1, []):
                j = zones.index(z2)
                matrix[i, j] = np.exp(-self.decay_factor * dist)
                
        # Normalize rows to represent valid transition probabilities (markov chain)
        row_sums = matrix.sum(axis=1)
        matrix = matrix / row_sums[:, np.newaxis]
        return matrix

    def _simulate_spread(self, initial_zones: dict[str, float], steps: int, transition_matrix: np.ndarray) -> dict[str, float]:
        """Simulate spread using Markov Chain propagation."""
        zones = list(initial_zones.keys())
        state_vector = np.array([initial_zones.get(z, 0.0) for z in zones])
        
        # Matrix power for steps
        powered_matrix = np.linalg.matrix_power(transition_matrix, max(1, steps))
        
        final_state = state_vector.dot(powered_matrix)
        
        return {z: float(final_state[i]) for i, z in enumerate(zones)}
