from __future__ import annotations
import time
import networkx as nx
from typing import Any
from app.core.logging import get_logger
from ..domain.models import ModelLineage

log = get_logger(__name__)

class ModelLineageTracker:
    def __init__(self) -> None:
        self._graph = nx.DiGraph()
        self._lineages: dict[str, ModelLineage] = {}

    async def register_lineage(self, model_id: str, parent_model_ids: list[str], training_datasets: list[str], feature_names: list[str], transformations: list[str]) -> ModelLineage:
        start_t = time.perf_counter()
        
        lineage = ModelLineage(
            model_id=model_id,
            parent_model_ids=parent_model_ids,
            training_datasets=training_datasets,
            feature_names=feature_names,
            transformations=transformations
        )
        
        self._lineages[model_id] = lineage
        self._graph.add_node(model_id)
        
        for parent_id in parent_model_ids:
            self._graph.add_edge(parent_id, model_id)
            
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Registered lineage for {model_id} in {latency:.2f}ms")
        return lineage

    async def get_lineage(self, model_id: str) -> ModelLineage | None:
        start_t = time.perf_counter()
        res = self._lineages.get(model_id)
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched lineage for {model_id} in {latency:.2f}ms")
        return res

    async def get_ancestors(self, model_id: str) -> list[str]:
        start_t = time.perf_counter()
        if model_id not in self._graph:
            return []
            
        res = list(nx.ancestors(self._graph, model_id))
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched ancestors for {model_id} in {latency:.2f}ms")
        return res

    async def get_descendants(self, model_id: str) -> list[str]:
        start_t = time.perf_counter()
        if model_id not in self._graph:
            return []
            
        res = list(nx.descendants(self._graph, model_id))
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched descendants for {model_id} in {latency:.2f}ms")
        return res

    async def get_lineage_depth(self, model_id: str) -> int:
        start_t = time.perf_counter()
        
        if model_id not in self._graph:
            return 0
            
        roots = [node for node, in_degree in self._graph.in_degree() if in_degree == 0]
        max_depth = 0
        
        for root in roots:
            try:
                # Find shortest path length from root to this model
                # Length in terms of edges is depth
                path_len = nx.shortest_path_length(self._graph, source=root, target=model_id)
                if path_len > max_depth:
                    max_depth = path_len
            except nx.NetworkXNoPath:
                continue
                
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Computed lineage depth for {model_id} in {latency:.2f}ms")
        return max_depth

    async def find_common_ancestor(self, model_id_a: str, model_id_b: str) -> str | None:
        start_t = time.perf_counter()
        
        if model_id_a not in self._graph or model_id_b not in self._graph:
            return None
            
        try:
            lca = nx.lowest_common_ancestor(self._graph, model_id_a, model_id_b)
            latency = (time.perf_counter() - start_t) * 1000
            log.info(f"Found common ancestor for {model_id_a} and {model_id_b} in {latency:.2f}ms")
            return str(lca) if lca else None
        except Exception as e:
            log.error(f"Error finding LCA: {e}")
            return None

    async def export_lineage_graph(self, model_id: str) -> dict[str, Any]:
        start_t = time.perf_counter()
        
        ancestors = await self.get_ancestors(model_id)
        descendants = await self.get_descendants(model_id)
        subgraph_nodes = set([model_id] + ancestors + descendants)
        
        subgraph = self._graph.subgraph(subgraph_nodes)
        
        nodes = list(subgraph.nodes())
        edges = list(subgraph.edges())
        depth = await self.get_lineage_depth(model_id)
        
        res = {
            "model_id": model_id,
            "nodes": nodes,
            "edges": [{"source": u, "target": v} for u, v in edges],
            "depth": depth
        }
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Exported lineage graph for {model_id} in {latency:.2f}ms")
        return res

_service_instance = None

def get_lineage_tracker() -> ModelLineageTracker:
    global _service_instance
    if _service_instance is None:
        _service_instance = ModelLineageTracker()
    return _service_instance
