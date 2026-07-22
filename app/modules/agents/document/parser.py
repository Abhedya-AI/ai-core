"""parser.py — Phase 2: Structural Document Parser."""

from typing import Any

from app.modules.agents.document.models import IngestedDocument
from app.modules.agents.document.providers import PDFProvider, WordProvider


class DocumentParser:
    """Phase 2: Extracts layout structure, headings, page numbers, and tables."""

    @staticmethod
    def parse(document: IngestedDocument) -> dict[str, Any]:
        if document.file_type == "PDF":
            return PDFProvider.parse_pdf(document.source_uri)
        return WordProvider.parse_word(document.source_uri)
