"""context_builder.py — Phase 11: Structured Prompt Context Builder."""

from app.modules.agents.document.models import DocumentChunk, ExtractedEntity


class ContextBuilder:
    """Phase 11: Constructs a structured prompt context combining graph facts, chunk excerpts, metadata, and citations."""

    @staticmethod
    def build_prompt_context(
        query: str,
        chunks: list[DocumentChunk],
        graph_nodes: list[str],
        entities: list[ExtractedEntity],
    ) -> str:
        """Build grounded prompt string for LLM generation."""
        lines = [
            f"User Query: {query}",
            "Knowledge Graph Entities & Nodes: " + ", ".join(graph_nodes),
            "Relevant Document Excerpts:",
        ]

        for c in chunks:
            lines.append(f"  [Chunk {c.chunk_id} | Page {c.page_number} | {c.section_title}]: {c.content}")

        return "\n".join(lines)
