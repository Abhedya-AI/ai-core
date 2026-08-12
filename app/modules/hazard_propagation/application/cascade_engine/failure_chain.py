from __future__ import annotations
import networkx as nx
from app.core.logging import get_logger

try:
    from app.modules.hazard_propagation.application.cascade_engine.cascade_detector import CascadeDetector
except ImportError:
    CascadeDetector = None

log = get_logger(__name__)

class FailureChainBuilder:
    """Builds and analyzes hazard failure chains."""

    def __init__(self, cascade_detector: CascadeDetector | None = None) -> None:
        self.detector = cascade_detector if cascade_detector else CascadeDetector()

    def build_failure_chain(self, initial_hazard_type: str, initial_intensity: float, zone_id: str, max_stages: int = 5) -> list[dict]:
        """Recursively build cascade chains."""
        chain = []
        
        def _build(hazard, intensity, prob, cumulative_time, stage):
            if stage > max_stages:
                return
                
            chain.append({
                "stage": stage,
                "hazard_type": hazard,
                "probability": prob,
                "cumulative_probability": self.compute_chain_probability(chain) if chain else prob,
                "time_minutes_from_start": cumulative_time
            })
            
            cascades = self.detector.detect_cascades(hazard, intensity, {})
            for c in cascades:
                _build(c["triggers"], c["intensity"], c["probability"], cumulative_time + c["time_minutes"], stage + 1)
                
        _build(initial_hazard_type, initial_intensity, 1.0, 0.0, 1)
        return chain

    def compute_chain_probability(self, chain: list[dict]) -> float:
        """Product of stage probabilities."""
        if not chain:
            return 0.0
        prob = 1.0
        for stage in chain:
            prob *= stage.get("probability", 1.0)
        return prob

    def find_critical_path(self, chains: list[list[dict]]) -> list[dict] | None:
        """Find chain with highest cumulative probability."""
        if not chains:
            return None
            
        best_chain = None
        best_prob = -1.0
        
        for chain in chains:
            prob = self.compute_chain_probability(chain)
            if prob > best_prob:
                best_prob = prob
                best_chain = chain
                
        return best_chain

    def compute_cascade_time(self, chain: list[dict]) -> float:
        """Sum of time_minutes from each stage."""
        if not chain:
            return 0.0
        # The chain might have cumulative time already, but assuming it's sum of deltas:
        # Based on rules, we'll just return the max time if they are cumulative, or sum if individual
        # Since _build uses cumulative, return the last stage's time
        return chain[-1].get("time_minutes_from_start", 0.0)

    def build_domino_graph(self, chain: list[dict]) -> nx.DiGraph:
        """Build directed graph from chain."""
        graph = nx.DiGraph()
        for i in range(len(chain) - 1):
            u = chain[i]["hazard_type"]
            v = chain[i+1]["hazard_type"]
            graph.add_edge(u, v, probability=chain[i+1]["probability"])
        return graph

    def identify_intervention_points(self, chain: list[dict]) -> list[dict]:
        """Identify points to break the chain."""
        interventions = []
        for i, stage in enumerate(chain):
            interventions.append({
                "stage_index": i,
                "hazard_type": stage["hazard_type"],
                "intervention_action": f"Mitigate {stage['hazard_type']}",
                "probability_reduction": 0.5
            })
        return interventions
