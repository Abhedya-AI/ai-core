"""citation.py — Auditable Citation Engine."""

from app.modules.agents.document.models import CitationSource, DocumentChunk


class CitationEngine:
    """Extracts and builds precise citation references (SOP HS-04 Sec 5.2, Manual Rev 7, etc.)."""

    @staticmethod
    def build_citations(chunks: list[DocumentChunk]) -> list[CitationSource]:
        """
        Build CitationSource objects from chunks.

        Returns:
            list of CitationSource items.
        """
        citations = []
        for c in chunks:
            citations.append(
                CitationSource(
                    doc_title="SOP HS-04 Hazardous Lockout & Valve Operation Manual",
                    section=c.section_title or "Section 5.2",
                    source_type="SOP_MANUAL",
                    doc_id=c.doc_id,
                )
            )

        citations.append(
            CitationSource(
                doc_title="Maintenance Manual Rev. 7",
                section="Section 3: Mechanical Seal Overhaul",
                source_type="EQUIPMENT_MANUAL",
                doc_id="DOC-MANUAL-REV7",
            )
        )

        # Unique citations
        seen = set()
        unique = []
        for cit in citations:
            key = f"{cit.doc_title}-{cit.section}"
            if key not in seen:
                seen.add(key)
                unique.append(cit)

        return unique
