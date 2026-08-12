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

class RiskPropagationForecaster:
    """Forecaster for estimating how risk diffuses through the system."""

    def __init__(self, knowledge_service=None) -> None:
        self.knowledge_service = knowledge_service

    async def forecast_risk_propagation(self, source_id: str, risk_value: float, horizon_hours: int) -> dict:
        """Forecast the propagation of risk across nodes using heat diffusion."""
        log.info(f"Forecasting risk propagation from {source_id} for {horizon_hours} hours")
        
        # Mock graph
        G = nx.Graph()
        G.add_edges_from([
            (source_id, "node_1"), (source_id, "node_2"),
            ("node_1", "node_3"), ("node_2", "node_3"),
            ("node_3", "node_4")
        ])
        
        nodes = list(G.nodes())
        n = len(nodes)
        
        adj_matrix = nx.to_numpy_array(G, nodelist=nodes)
        
        initial_heat = np.zeros(n)
        if source_id in nodes:
            initial_heat[nodes.index(source_id)] = risk_value
            
        final_heat = self._graph_heat_diffusion(adj_matrix, initial_heat, max(1, horizon_hours))
        
        propagated_risks = {nodes[i]: float(np.clip(final_heat[i], 0.0, 1.0)) for i in range(n)}
        
        # Filter zero risks
        propagated_risks = {k: v for k, v in propagated_risks.items() if v > 0.01}
        
        highest_impact_nodes = sorted(propagated_risks.keys(), key=lambda x: propagated_risks[x], reverse=True)[:5]
        
        total_system_risk = float(np.sum(list(propagated_risks.values())))
        
        # Determine risk paths (simple shortest paths from source to impacted)
        risk_paths = []
        if source_id in G:
            for target in highest_impact_nodes:
                if target != source_id:
                    try:
                        path = nx.shortest_path(G, source=source_id, target=target)
                        risk_paths.append(path)
                    except nx.NetworkXNoPath:
                        pass
        
        return {
            "propagated_risks": propagated_risks,
            "highest_impact_nodes": highest_impact_nodes,
            "total_system_risk": total_system_risk,
            "risk_paths": risk_paths
        }

    def _graph_heat_diffusion(self, adjacency_matrix: np.ndarray, initial_heat: np.ndarray, steps: int) -> np.ndarray:
        """Compute heat diffusion using Graph Laplacian."""
        degrees = np.sum(adjacency_matrix, axis=1)
        D = np.diag(degrees)
        L = D - adjacency_matrix
        
        # Heat equation: H(t) = H(0) * e^(-Lt)
        # Using discrete approximation for steps
        # H(t+1) = H(t) - alpha * L * H(t)
        alpha = 0.1  # diffusion rate
        
        heat = initial_heat.copy()
        for _ in range(steps):
            delta = alpha * L.dot(heat)
            heat = heat - delta
            heat = np.clip(heat, 0.0, 1.0) # Ensure heat stays within [0, 1]
            
        return heat
