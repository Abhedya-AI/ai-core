"""graph_retriever.py — Knowledge Graph Retriever."""

from typing import Any

from app.core.logging import get_logger
from app.modules.graphrag.query.parser import ParsedQuery
from app.modules.knowledge.services.traversal_service import TraversalService

log = get_logger("graphrag.retrieval.graph")


class GraphRetriever:
    """Retrieves structured subgraphs and k-hop neighborhood facts from the Knowledge Graph."""

    def __init__(self, traversal_svc: TraversalService | None = None) -> None:
        self._traversal = traversal_svc or TraversalService()

    async def retrieve_graph_facts(self, parsed_query: ParsedQuery, max_depth: int = 2) -> list[dict[str, Any]]:
        """
        Retrieve graph facts for extracted entity IDs or target entity types.

        Returns:
            list of node and edge dictionaries retrieved from the graph.
        """
        facts: list[dict[str, Any]] = []

        if not parsed_query.entity_ids:
            log.debug("No target entity IDs extracted for graph retrieval")
            return facts

        for entity_id in parsed_query.entity_ids[:3]:
            try:
                res = await self._traversal.traverse_khop(entity_id, max_depth=max_depth)
                for path in res.paths:
                    for node in path.nodes:
                        node["_retrieved_via"] = "graph_traversal"
                        facts.append(node)
            except Exception as exc:
                log.warning(f"Graph retrieval failed for entity '{entity_id}': {exc}")

        return facts
