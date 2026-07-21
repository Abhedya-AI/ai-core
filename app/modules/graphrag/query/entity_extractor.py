"""entity_extractor.py — Entity Extractor for industrial safety queries."""

import re

from app.modules.knowledge.domain.ontology import ENTITY_TYPES


class EntityExtractor:
    """Extracts entity IDs, equipment codes, zone codes, and entity types from natural language queries."""

    @staticmethod
    def extract_entities(query_text: str) -> dict[str, list[str]]:
        """
        Extract entities from query text.

        Returns:
            dict containing lists of extracted 'entity_ids', 'entity_types', and 'keywords'.
        """
        extracted_ids = set()
        extracted_types = set()

        # Regex pattern for ID codes (e.g. Tank T-12, EQ-101, W-12, Z-1, HAZ-99, S-4, SENSOR-12)
        code_pattern = r"\b(?:[A-Z]{1,4}-\d+|Tank\s+[A-Z0-9-]+|Zone\s+[A-Z0-9-]+)\b"
        matches = re.findall(code_pattern, query_text, re.IGNORECASE)
        for m in matches:
            extracted_ids.add(m.strip())

        # Match against known Ontology entity labels
        for entity_label in ENTITY_TYPES:
            if re.search(r"\b" + re.escape(entity_label) + r"s?\b", query_text, re.IGNORECASE):
                extracted_types.add(entity_label)

        return {
            "entity_ids": list(extracted_ids),
            "entity_types": list(extracted_types),
        }
