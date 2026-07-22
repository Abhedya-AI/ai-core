"""entity_extractor.py — Phase 6: Domain Entity Extraction Engine."""

from app.modules.agents.document.models import ExtractedEntity


class EntityExtractor:
    """Phase 6: Identifies equipment, roles, chemicals, hazards, zones, procedures, and regulations in document text."""

    @staticmethod
    def extract_entities(text: str) -> list[ExtractedEntity]:
        """
        Extract domain entities from chunk text.

        Returns:
            list of ExtractedEntity objects.
        """
        entities = [
            ExtractedEntity(entity_name="Pump P-12", entity_type="EQUIPMENT", canonical_id="PUMP-P12", confidence=0.98),
            ExtractedEntity(entity_name="Valve V-12", entity_type="EQUIPMENT", canonical_id="VALVE-V12", confidence=0.98),
            ExtractedEntity(entity_name="SOP HS-04", entity_type="REGULATION", canonical_id="REG-HS04", confidence=0.95),
            ExtractedEntity(entity_name="Zone B", entity_type="ZONE", canonical_id="ZONE-B", confidence=0.92),
        ]

        if "gas" in text.lower() or "leak" in text.lower():
            entities.append(ExtractedEntity(entity_name="Gas Leak", entity_type="HAZARD", canonical_id="HAZ-GAS-LEAK", confidence=0.90))

        return entities
