"""graph_provider.py — Graph Context Compliance Provider."""

from typing import Any


class GraphComplianceProvider:
    """Extracts entity relationships and zone permissions from Knowledge Graph."""

    @staticmethod
    def get_graph_context(context_graph: dict[str, Any]) -> list[dict[str, Any]]:
        facts = []
        if context_graph:
            for k, v in context_graph.items():
                facts.append({"entity_id": k, "relations": v})
        return facts
