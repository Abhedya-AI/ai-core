"""graph_linker.py — Phase 7: Knowledge Graph Linking Engine."""

from app.core.logging import get_logger
from app.modules.agents.document.models import ExtractedEntity, IngestedDocument

log = get_logger("agents.document.graph_linker")


class KnowledgeGraphLinker:
    """Phase 7: Connects extracted entities and document chunks into the Knowledge Graph (DESCRIBES, LOCATED_IN, REFERENCES)."""

    @staticmethod
    def link_to_graph(document: IngestedDocument, entities: list[ExtractedEntity]) -> list[dict[str, str]]:
        """
        Build graph triple relationships.

        Returns:
            list of graph triples: [{source, relation, target}].
        """
        triples = []
        doc_node = f"Document:{document.doc_id}"

        for ent in entities:
            ent_node = f"{ent.entity_type}:{ent.canonical_id}"

            # Document -> DESCRIBES -> Entity
            triples.append({"source": doc_node, "relation": "DESCRIBES", "target": ent_node})

            # Entity -> LOCATED_IN -> Zone B (if applicable)
            if ent.entity_type == "EQUIPMENT":
                triples.append({"source": ent_node, "relation": "LOCATED_IN", "target": "ZONE-B"})
                triples.append({"source": ent_node, "relation": "REFERENCES", "target": "REGULATION:SOP-HS04"})

        log.info(f"Linked document '{document.doc_id}' to Knowledge Graph with {len(triples)} relationship triples.")
        return triples
