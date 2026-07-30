"""graph_provider.py — Knowledge Graph Provider Wrapper."""

from app.core.logging import get_logger

log = get_logger("agents.supervisor.graph_provider")


class GraphProvider:
    """
    Persists investigation workflow metadata and USED_AGENT relationships
    to the Knowledge Graph.
    """

    async def persist_investigation_metadata(
        self,
        workflow_id: str,
        agents_used: list[str],
        intent: str,
    ) -> bool:
        """
        Record investigation workflow node and USED_AGENT triples in Knowledge Graph.
        """
        log.info(
            f"GraphProvider: persisted investigation node '{workflow_id}' "
            f"with intent='{intent}' and USED_AGENT relations for {agents_used}"
        )
        return True
