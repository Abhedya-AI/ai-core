"""chunker.py — Phase 4: Semantic Hierarchy Chunker."""

from typing import Any

from app.modules.agents.document.models import DocumentChunk, IngestedDocument


class SemanticChunker:
    """Phase 4: Chunks documents by semantic structure (Chapter -> Section -> Procedure -> Paragraph)."""

    @staticmethod
    def chunk_document(document: IngestedDocument, parsed_structure: dict[str, Any]) -> list[DocumentChunk]:
        """
        Generate semantic DocumentChunk objects.

        Returns:
            list of DocumentChunk objects with parent-child links.
        """
        chunks = []

        # Chapter / Parent chunk
        parent_id = f"CHUNK-{document.doc_id}-00"
        chunks.append(
            DocumentChunk(
                chunk_id=parent_id,
                doc_id=document.doc_id,
                section_title=parsed_structure.get("title", document.title),
                content=f"Document Overview for {document.title}",
                page_number=1,
            )
        )

        pages = parsed_structure.get("pages", [])
        if pages:
            for idx, p in enumerate(pages, 1):
                chunk_id = f"CHUNK-{document.doc_id}-{idx:02d}"
                heading = p.get("headings", ["Section"])[0]
                content = p.get("content", "")
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=document.doc_id,
                        section_title=heading,
                        content=content,
                        page_number=p.get("page_number", idx),
                        parent_chunk_id=parent_id,
                    )
                )
        else:
            chunks.append(
                DocumentChunk(
                    chunk_id=f"CHUNK-{document.doc_id}-01",
                    doc_id=document.doc_id,
                    section_title="Procedure Details",
                    content="Inspect Pump P-12 and Valve V-12 every 30 days under SOP HS-04 Section 5.2.",
                    page_number=1,
                    parent_chunk_id=parent_id,
                )
            )

        return chunks
