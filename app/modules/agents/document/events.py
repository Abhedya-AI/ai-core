"""events.py — Standardized Document Domain Event Generator."""

from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.document.models import IngestedDocument


class DocumentEventGenerator:
    """Generates standardized document domain events for the EventBus."""

    @staticmethod
    def generate_events(
        agent_name: str,
        doc: IngestedDocument,
        chunks_count: int,
        trace_id: str,
    ) -> list[AgentDomainEvent]:
        """
        Generate document domain events.

        Returns:
            list of AgentDomainEvent objects (DocumentIndexed, KnowledgeExtracted, EmbeddingCreated, GraphUpdated).
        """
        return [
            AgentDomainEvent(
                event_type="DocumentIndexed",
                agent_name=agent_name,
                payload={"doc_id": doc.doc_id, "title": doc.title, "file_type": doc.file_type},
                trace_id=trace_id,
            ),
            AgentDomainEvent(
                event_type="KnowledgeExtracted",
                agent_name=agent_name,
                payload={"doc_id": doc.doc_id, "entities_count": len(doc.extracted_entities)},
                trace_id=trace_id,
            ),
            AgentDomainEvent(
                event_type="EmbeddingCreated",
                agent_name=agent_name,
                payload={"doc_id": doc.doc_id, "chunks_count": chunks_count},
                trace_id=trace_id,
            ),
            AgentDomainEvent(
                event_type="GraphUpdated",
                agent_name=agent_name,
                payload={"doc_id": doc.doc_id, "relations_linked": len(doc.extracted_entities) * 3},
                trace_id=trace_id,
            ),
        ]
