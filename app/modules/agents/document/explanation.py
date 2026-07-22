"""explanation.py — XAI Explanation Generator."""

from app.modules.agents.document.models import GroundedAnswer


class DocumentExplanationGenerator:
    """Generates auditable XAI explanations detailing retrieved graph nodes, document chunks, and citations."""

    @staticmethod
    def generate_explanation(grounded_answer: GroundedAnswer) -> str:
        lines = [
            "GraphRAG Grounded Response Report",
            f"Retrieved Graph Nodes: {', '.join(grounded_answer.graph_evidence_nodes)}",
            f"Retrieved Document Chunks: {', '.join(grounded_answer.retrieved_chunk_ids)}",
            "Auditable Citations:",
        ]

        for cit in grounded_answer.citations:
            lines.append(f"  • {cit.doc_title} ({cit.section}) [{cit.source_type}]")

        lines.append(f"Confidence Score: {round(grounded_answer.confidence * 100, 1)}%")
        return "\n".join(lines)
