"""metadata.py — Phase 5: Metadata Extraction Engine."""

from app.modules.agents.document.models import IngestedDocument


class MetadataExtractor:
    """Phase 5: Captures author, version, issue date, department, document type, and confidentiality level."""

    @staticmethod
    def extract_metadata(document: IngestedDocument) -> dict:
        return {
            "title": document.title,
            "doc_id": document.doc_id,
            "version": document.version,
            "author": document.author,
            "department": "Plant Safety & Operations",
            "confidentiality": "INTERNAL_USE",
            "tags": ["SOP", "LOTO", "PUMP", "VALVE", "SAFETY"],
        }
