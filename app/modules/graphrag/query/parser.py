"""parser.py — Query Parser and DTO."""

from typing import Any

from pydantic import BaseModel, Field

from app.modules.graphrag.query.entity_extractor import EntityExtractor
from app.modules.graphrag.query.intent import QueryIntent


class ParsedQuery(BaseModel):
    """Parsed representation of a user query."""

    raw_query: str
    intent: QueryIntent = QueryIntent.GENERAL_SAFETY
    entity_ids: list[str] = Field(default_factory=list)
    entity_types: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class QueryParser:
    """Parses natural language queries into intent and extracted entities."""

    @staticmethod
    def parse(query_text: str) -> ParsedQuery:
        """Parse query into structured intent and entity targets."""
        q_lower = query_text.lower()

        # Intent classification heuristics
        if any(w in q_lower for w in ["risk", "hazard", "leak", "threat", "danger", "spread"]):
            intent = QueryIntent.RISK_ANALYSIS
        elif any(w in q_lower for w in ["incident", "explosion", "root cause", "failure", "investigate"]):
            intent = QueryIntent.INCIDENT_INVESTIGATION
        elif any(w in q_lower for w in ["evacuate", "evacuation", "emergency", "escape"]):
            intent = QueryIntent.EVACUATION_PLAN
        elif any(w in q_lower for w in ["permit", "osha", "regulation", "compliance", "policy"]):
            intent = QueryIntent.COMPLIANCE_CHECK
        elif any(w in q_lower for w in ["equipment", "machine", "pump", "sensor", "valve", "status", "health"]):
            intent = QueryIntent.EQUIPMENT_STATUS
        else:
            intent = QueryIntent.GENERAL_SAFETY

        extracted = EntityExtractor.extract_entities(query_text)
        words = [w.strip() for w in re.findall(r"\w+", query_text) if len(w) > 3]

        return ParsedQuery(
            raw_query=query_text,
            intent=intent,
            entity_ids=extracted["entity_ids"],
            entity_types=extracted["entity_types"],
            keywords=words,
        )


import re  # ensure regex import
